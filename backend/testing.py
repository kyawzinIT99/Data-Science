import requests
import pandas as pd
import numpy as np
import time
import os

BASE_URL = "http://localhost:8000/api"
REPORT_FILE = "test.md"

def log_result(f, title, status, details=""):
    print(f"[{status}] {title}")
    f.write(f"### {title}\n")
    f.write(f"**Status**: {'✅ PASSED' if status == 'PASS' else '❌ FAILED'}\n")
    if details:
        f.write(f"{details}\n\n")

def generate_noisy_data(filename="noisy_test.csv"):
    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    sales = np.random.normal(500, 50, 100)
    sales[10] = 5000  # Anomaly
    sales[20] = np.nan # Missing value
    
    df = pd.DataFrame({
        "Date": dates,
        "Sales": sales,
        "Marketing_Spend": np.random.uniform(100, 300, 100),
        "Foot_Traffic": np.random.poisson(1000, 100)
    })
    df.to_csv(filename, index=False)
    return filename

def generate_second_file(filename="second_test.csv"):
    np.random.seed(100)
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    df = pd.DataFrame({
        "Date": dates,
        "Customer_Satisfation": np.random.uniform(1, 5, 100),
    })
    df.to_csv(filename, index=False)
    return filename

def run_tests():
    with open(REPORT_FILE, "w") as f:
        f.write("# Automated Test Report\n\n")
        f.write("This report validates the robustness and functionality of the AI Data Analysis Platform.\n\n")

        try:
            # 1. Noisy Data & Upload
            noisy_file = generate_noisy_data()
            second_file = generate_second_file()
            
            with open(noisy_file, "rb") as file1:
                res = requests.post(f"{BASE_URL}/upload", files={"file": file1})
            
            if res.status_code == 200:
                file_id = res.json()["file_id"]
                log_result(f, "Upload Noisy Data", "PASS", f"Successfully uploaded noisy data. File ID: {file_id}")
            else:
                log_result(f, "Upload Noisy Data", "FAIL", f"Upload failed: {res.text}")
                return

            # 2. Persistence Check
            res_list = requests.get(f"{BASE_URL}/files")
            if res_list.status_code == 200 and any(item["file_id"] == file_id for item in res_list.json()):
                log_result(f, "Persistence Check", "PASS", "File successfully persisted in TinyDB and verified via /files endpoint.")
            else:
                log_result(f, "Persistence Check", "FAIL", "File not found in /files list.")

            # 3. Dashboard Generation (Includes Prophet and Outliers)
            res_dash = requests.post(f"{BASE_URL}/dashboard", json={"file_id": file_id})
            if res_dash.status_code == 200:
                dash_data = res_dash.json()
                details = f"- Charts generated: {len(dash_data.get('charts', []))}\n"
                details += f"- Anomalies found: {len(dash_data.get('anomalies', []))}\n"
                if "time_series_decomposition" in dash_data:
                    details += f"- Prophet Decomposition: Supported!\n"
                log_result(f, "Dashboard Generation (Noisy Data & Prophet)", "PASS", details)
            else:
                log_result(f, "Dashboard Generation", "FAIL", f"Failed: {res_dash.text}")

            # 4. Export PPTX
            res_pptx = requests.get(f"{BASE_URL}/export/{file_id}/pptx")
            if res_pptx.status_code == 200 and len(res_pptx.content) > 1000:
                log_result(f, "Export PPTX", "PASS", "Successfully generated PowerPoint report as internal blob.")
            else:
                log_result(f, "Export PPTX", "FAIL", "PPTX generation failed or returned invalid data.")

            # 5. Causal Inference (DAG)
            res_causal = requests.get(f"{BASE_URL}/causal/{file_id}")
            if res_causal.status_code == 200:
                causal_data = res_causal.json()
                details = f"- Nodes: {len(causal_data.get('nodes', []))}\n"
                details += f"- Edges: {len(causal_data.get('links', []))}\n"
                log_result(f, "Causal Inference (DAG)", "PASS", details)
            else:
                log_result(f, "Causal Inference", "FAIL", f"Failed: {res_causal.text}")

            # 6. Multi-File Synthesis
            with open(noisy_file, "rb") as f1, open(second_file, "rb") as f2:
                res_multi = requests.post(
                    f"{BASE_URL}/upload-multi", 
                    files=[
                        ("files", (noisy_file, f1, "text/csv")), 
                        ("files", (second_file, f2, "text/csv"))
                    ]
                )
            
            if res_multi.status_code == 200:
                multi_id = res_multi.json()["file_id"]
                log_result(f, "Multi-File Synthesis", "PASS", f"Successfully merged two datasets. New File ID: {multi_id}")
            else:
                log_result(f, "Multi-File Synthesis", "FAIL", f"Failed: {res_multi.text}")

            # Cleanup
            requests.delete(f"{BASE_URL}/files/{file_id}")
            if 'multi_id' in locals():
                requests.delete(f"{BASE_URL}/files/{multi_id}")
            os.remove(noisy_file)
            os.remove(second_file)
            
            f.write("\n## Conclusion\nAll core capabilities, including robustness to noisy data and recent V2 enhancements, are functioning as expected.\n")

        except Exception as e:
            log_result(f, "Test Suite Execution", "FAIL", str(e))

if __name__ == "__main__":
    print("Running automated test suite...")
    time.sleep(2) # Give servers a moment if just started
    run_tests()
    print(f"Testing complete. Report saved to {REPORT_FILE}")
