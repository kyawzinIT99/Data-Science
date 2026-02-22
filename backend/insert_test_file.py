import uuid
import os
import shutil
from datetime import datetime, timezone
from app.core.database import files_table

# Setup paths
src_file = "audit_stress_test_high_scale.csv"
file_id = str(uuid.uuid4())
dest_file = f".storage/uploads/{file_id}.csv"

# Copy file
shutil.copy2(src_file, dest_file)

# Insert DB record
file_size = os.path.getsize(dest_file)
files_table.insert({
    "file_id": file_id,
    "filename": "Direct_Injection_20k_Test.csv",
    "file_type": "csv",
    "num_chunks": 1, 
    "uploaded_at": datetime.now(timezone.utc).isoformat(),
    "file_size": file_size,
})
print("File successfully injected into the database!")
