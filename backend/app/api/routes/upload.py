from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException
import os

from app.core.database import files_table, File as FileQ
from app.services.file_parser import validate_file, save_uploaded_file, extract_text
from app.services.chunker import chunk_text, create_vectorstore
from app.models.schemas import FileUploadResponse, FileRecord

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    # Validate before processing if possible
    file_size = file.size if hasattr(file, 'size') and file.size is not None else 0
    valid, error = validate_file(file.filename, file_size)
    if not valid:
        raise HTTPException(status_code=400, detail=error)

    from app.services.file_parser import save_uploaded_file_stream
    file_id, file_path = await save_uploaded_file_stream(file, file.filename)

    text = extract_text(file_path)
    if not text.strip():
        # Clean up failed file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    chunks = chunk_text(text)
    create_vectorstore(file_id, chunks)

    # Save file record to database
    files_table.insert({
        "file_id": file_id,
        "filename": file.filename,
        "file_type": file.filename.rsplit(".", 1)[-1],
        "num_chunks": len(chunks),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "file_size": os.path.getsize(file_path),
    })

    return FileUploadResponse(
        file_id=file_id,
        filename=file.filename,
        file_type=file.filename.rsplit(".", 1)[-1],
        num_chunks=len(chunks),
        preview=text[:500],
    )

@router.post("/upload-multi", response_model=FileUploadResponse)
async def upload_multi_files(files: list[UploadFile] = File(...)):
    import pandas as pd
    import uuid
    import os
    from app.services.file_parser import get_file_extension, save_uploaded_file_stream
    from app.core.config import settings

    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Please upload at least 2 files to merge")
    
    dfs = []
    temp_files = []
    for _file in files:
        file_size = _file.size if hasattr(_file, 'size') and _file.size is not None else 0
        valid, error = validate_file(_file.filename, file_size)
        if not valid:
            raise HTTPException(status_code=400, detail=f"{_file.filename}: {error}")
            
        file_id, file_path = await save_uploaded_file_stream(_file, _file.filename)
        temp_files.append(file_path)
        
        ext = get_file_extension(_file.filename)
        try:
            if ext == ".csv":
                try:
                    df = pd.read_csv(file_path)
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='latin1')
            elif ext in (".xlsx", ".xls"):
                try:
                    df = pd.read_excel(file_path)
                except Exception:
                    try:
                        df = pd.read_excel(file_path, engine='openpyxl')
                    except Exception:
                        df = pd.read_excel(file_path, engine='xlrd')
            else:
                continue # Skip non-tabular 
            dfs.append(df)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading {_file.filename}: {str(e)}")
            
    if not dfs:
        raise HTTPException(status_code=400, detail="No valid tabular data found to merge")
        
    common_cols = list(set.intersection(*[set(df.columns) for df in dfs]))
    if common_cols and len(common_cols) > 0 and len(common_cols) < len(dfs[0].columns):
        merged_df = dfs[0]
        for df in dfs[1:]:
            merged_df = pd.merge(merged_df, df, on=common_cols[0], how='outer', suffixes=('', '_dup'))
    else:
        merged_df = pd.concat(dfs, axis=1)
        
    merged_df = merged_df.loc[:,~merged_df.columns.duplicated()]

    merged_id = f"merged_{uuid.uuid4().hex[:8]}"
    merged_filename = f"merged_dataset_{len(files)}.csv"
    merged_path = os.path.join(settings.UPLOAD_DIR, f"{merged_id}.csv")

    # --- Modal Remote Execution Hook ---
    from app.utils.modal import get_modal_func, sync_file_to_modal
    modal_merge_run = get_modal_func("run_data_merge")
    if modal_merge_run:
        try:
            file_ids = []
            file_exts = []
            for f_path in temp_files:
                f_id = os.path.basename(f_path).rsplit(".", 1)[0]
                f_ext = os.path.splitext(f_path)[1].lower()
                if sync_file_to_modal(f_id, f_path):
                    file_ids.append(f_id)
                    file_exts.append(f_ext)
            
            if len(file_ids) == len(temp_files):
                logger.info(f"Offloading multi-file merge to Modal ({len(file_ids)} files)...")
                remote_result = modal_merge_run.remote(file_ids, file_exts)
                # Note: The merged file is now on the Modal volume.
                # We should eventually sync it back if needed, but for now we'll rely on it being there.
                # To keep local DB happy, we'll create an empty placeholder or download it.
                # For now, let's just use the local merged_df we already have to avoid blocking.
                pass 
        except Exception as e:
            logger.warning(f"Modal merge failed, using local: {e}")

    merged_df.to_csv(merged_path, index=False)
    
    text = extract_text(merged_path)
    if not text.strip():
        text = "Merged Dataset"
    chunks = chunk_text(text)
    create_vectorstore(merged_id, chunks)

    file_size = os.path.getsize(merged_path)

    files_table.insert({
        "file_id": merged_id,
        "filename": merged_filename,
        "file_type": "csv",
        "num_chunks": len(chunks),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "file_size": file_size,
    })

    return FileUploadResponse(
        file_id=merged_id,
        filename=merged_filename,
        file_type="csv",
        num_chunks=len(chunks),
        preview=text[:500],
    )


@router.get("/files", response_model=list[FileRecord])
async def list_files():
    docs = files_table.all()
    records = []
    for d in sorted(docs, key=lambda x: x.get("uploaded_at", ""), reverse=True):
        records.append(FileRecord(**d))
    return records


@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    removed = files_table.remove(FileQ.file_id == file_id)
    if not removed:
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "deleted"}
