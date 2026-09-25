# Member Role Report — Day 10: Data Pipeline & Data Observability

> Báo cáo cá nhân của thành viên đảm nhận 2 vai trò: Observability Owner và Corruption & Integration Owner.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Thu Trang             |
| MSSV               | 2A202602435                     |
| Khóa/Lớp         | K4-L3              |
| Tên nhóm         | NhomChill     |
| Vai trò chính    | Observability owner & Corruption & integration owner                 |
| Repository         | K4-L3-DAY10-NhomChill-DataPipeline |
| Ngày hoàn thành | 2026-09-25               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Xây dựng Data Quality & Freshness Gate | `src/observability/quality.py` | Dataframe (`papers_clean.csv`) | Kết quả `quality_report.json`, `freshness_report.json` | Hoàn thành |
| Báo cáo tự động (Reporting) | `src/observability/reporting.py` | Metrics, logs, quality checks từ các bước | `phase1_report.md`, `corruption_report.md` | Hoàn thành |
| Kịch bản phá hỏng dữ liệu (Corruption) | `src/ingestion/corruption.py` | Dataframe chuẩn (baseline) | `corrupted_dataset.csv`, `corruption_log.json` | Hoàn thành |
| Lắp ráp luồng dữ liệu (Orchestration) | `phase1.py` & `corruption_flow.py` | Code của tất cả thành viên khác | Pipeline chạy mượt mà từ end-to-end | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Đấu nối Evaluate LLM | Thành viên 2 & 4 (Evaluation) | Cập nhật gọi trực tiếp hàm `evaluate_pipeline` vào `phase1.py` và `corruption_flow.py` thay vì dùng dữ liệu mock cứng. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Xây dựng Quality Gate bằng GX | `src/observability/quality.py` | Báo cáo `.json` (`baseline_gx_report.json`, v.v.) | Chạy `python script/run_phase1.py` kiểm tra file report |
| Xây dựng Báo cáo Markdown | `src/observability/reporting.py` | File `phase1_report.md`, `corruption_report.md` | Mở thư mục `data/reports/` |
| Orchestration & Đứt gãy | `src/pipelines/corruption_flow.py` | Pipeline chạy mượt mà 3 phase | Chạy `python script/run_corruption_flow.py` |

**Nêu một output cụ thể:**
Artifact `data/reports/corruption_report.md` tổng hợp bảng đối chiếu 3 cột metrics (Baseline, Corrupted, Repaired). Nó chứng minh rõ ràng khả năng của hệ thống RAG suy giảm do dữ liệu rác và phục hồi lại như cũ nhờ Idempotent Pipeline.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Nếu không có Observability, hệ thống sẽ ngầm đưa rác (văn bản trống, bài báo quá cũ) vào DB. Đồng thời, cần phải lắp ghép code (Integration) của mọi thành viên vào một chu trình tự động (Orchestration) và mô phỏng đứt gãy để kiểm thử hệ thống.

### Cách triển khai
- **Observability:** Sử dụng `great_expectations` (GX) để xây dựng suite bắt lỗi: `ExpectColumnValuesToNotBeNull`, `ExpectColumnValuesToBeUnique` (trên `paper_id`), và `ExpectColumnValueLengthsToBeBetween` (summary > 30 kí tự).
- **Freshness:** Code logic kiểm tra `age_days > 180` (lớn hơn 6 tháng). Nếu tỉ lệ bài báo cũ (`stale_ratio`) vượt quá ngưỡng 25% thì báo cờ `is_fresh = False`.
- **Corruption:** Dùng `.iloc` xóa 5 dòng đầu (drop), làm trống cột summary 5 dòng (`blank summary`), nhân bản (duplicate) 5 dòng và cộng thêm 200 vào cột `age_days` để giả lập sự cố.
- **Orchestration:** Lắp ghép code từ các module bằng cách import hàm, thiết lập Logging `logger.info`, gọi hàm từ việc Fetch dữ liệu đến Build Chroma Index.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Dataframe (`papers_clean.csv`), Metric JSON           |
| Output                         | Log, File `.json` báo cáo, Bảng `.md` so sánh |
| Module phụ thuộc             | `cleaning.py`, `metrics.py`, `crossref.py`                    |
| Module sử dụng output        | `data/reports/` (cho Giảng viên & người dùng đọc)                    |
| Điều kiện lỗi cần xử lý | API LLM bị Rate Limit khi chạy Eval; Lỗi thư viện GX                   |

### Cách xác minh

```bash
python script/run_corruption_flow.py
```
- **Kết quả mong đợi:** Khởi chạy 8 bước, corrupt data, check quality rớt, tái cấu trúc (repair) từ data raw và check quality pass. Sinh báo cáo `corruption_report.md`.
- **Kết quả thực tế:** Chạy thành công. Terminal hiện logs "Corruption flow complete!".
- **Artifact/log:** `data/reports/corruption_report.md` và thư mục `data/quality/`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Chọn công cụ để chạy Data Quality Checks.
- **Các phương án đã cân nhắc:** Dùng các câu lệnh kiểm tra của Pandas (`df.isnull().sum()`) HOẶC tích hợp thư viện `great_expectations`.
- **Phương án đã chọn:** Sử dụng `great_expectations` (GX).
- **Lý do:** Trade-off về độ phức tạp code ban đầu cao hơn so với dùng Pandas chay, nhưng GX cung cấp chuẩn mực (Expectation Suites) rất dễ mở rộng (như unique, value length), sinh metadata report `.json` chuyên nghiệp và minh bạch để chặn data rác.
- **Bằng chứng:** Code sử dụng `context.suites.add(gx.ExpectationSuite)` ở trong file `src/observability/quality.py`, sinh ra file báo cáo `.json` rất tường minh (True/False).

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `429 RESOURCE_EXHAUSTED. Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests...`
- **Lệnh hoặc bước tái hiện:** `python script/run_phase1.py` hoặc `run_corruption_flow.py`.
- **Nguyên nhân gốc:** Khi chạy Evaluate Testset, API Key miễn phí của Gemini chỉ cho phép 15 requests/phút. Testset có 24 câu hỏi, khiến vòng lặp gọi AI bị nghẽn (Rate Limit).
- **Cách xử lý:** Nhờ cơ chế Client của thư viện đã có tích hợp sẵn chức năng tự động Retry with Exponential Backoff (như log in ra: `Retrying in 46s...`). Mình quyết định không hủy quá trình đang chạy (không gõ Ctrl+C) mà kiên nhẫn để thư viện ngủ đông (sleep) rồi tự gọi lại Google API. (Nếu LLM vẫn tạch, hệ thống `metrics.py` cũng đã có fallback về Token F1).
- **Cách xác minh sau khi sửa:** Log hiển thị `200 OK` sau các lần Retry và báo cáo được sinh ra hoàn chỉnh.
- **Điều học được:** Khả năng chịu lỗi (Resilience) trong Data Pipeline rất quan trọng. Khi phụ thuộc vào dịch vụ AI qua mạng, luôn phải đối mặt với giới hạn quota và cần cơ chế Retry.

## 7. Hiểu biết về luồng end-to-end

1. Dữ liệu từ Crossref API (chứa ở `raw_records.json`) đi qua `cleaning.py` để thành `papers_clean.csv`. Chuỗi văn bản gộp `text_for_embedding` được trích xuất và biến thành vector (bởi model `all-MiniLM-L6-v2`) rồi đẩy vào cơ sở dữ liệu `ChromaDB`.
2. Evaluation set chứa `ground_truth` (câu trả lời chuẩn) và `ground_truth_doc_ids` (ID của bài báo gốc). ChromaDB sẽ dùng câu hỏi để tìm (Retrieve), nếu ID nó tìm ra trùng khớp với `ground_truth_doc_ids` thì sẽ tính là Hit. Câu trả lời của LLM được đối chiếu với `ground_truth` để chấm độ chính xác (Judge Score / F1).
3. Quality checks (GX) kiểm tra "Hình thức & Ngữ nghĩa cơ sở" của dữ liệu (như cấm null, ID không trùng lặp, summary đủ 30 kí tự). Freshness check chỉ tập trung kiểm tra "Sự lỗi thời" (Staleness) dựa trên cột thời gian xuất bản so với hiện tại.
4. Phải dùng cùng một Test Set xuyên suốt các Phase để đảm bảo tính công bằng (Fairness). Nếu Test Set thay đổi, ta không thể biết Hit Rate rớt là do dữ liệu rác (Corrupted) hay do bộ test mới hỏi quá khó.
5. Repair được xem là thành công khi `Quality Gate = True`, `is_fresh = True` và các thông số `retrieval_hit_rate`, `mean_token_f1` phục hồi tuyệt đối về 1.0 (như Baseline ban đầu) ghi trong file `corruption_report.md`.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |      1.0 |       0.7917 |      1.0 | Rớt hơn 20% do bị xoá mất 5 dòng và xoá trắng summary 5 dòng. Mất content nên DB không retrieve được. |
| `mean_token_f1`      |      1.0 |       0.8271 |      1.0 | Sai số gia tăng. Khi không có context đúng, Agent sinh ra từ vựng sai lệch. |
| `judge_accuracy`     |      1.0 |       0.8333 |      1.0 | Giám khảo Gemini chấm rớt vì Agent trả lời thiếu chính xác. Đã phục hồi hoàn hảo về 1.0. |
| `mean_judge_score`   |      5.0 |       4.25 |      5.0 | Từ điểm tuyệt đối (5.0), rớt xuống mức khá (4.25). |
| Quality checks         |      True |       False |      True | Bắt lỗi hoàn hảo nhờ cấu hình Great Expectations. |
| Freshness status       |      True |       False |      True | Phát hiện ôi thiu lập tức khi dữ liệu bị cộng thêm 200 ngày. |

### Kết luận từ số liệu

1. Dữ liệu bị tiêm rác (xóa dòng, rỗng chữ) → **Quality Gate phát cờ False** → RAG Hit Rate rớt xuống 0.79 và Accuracy tụt xuống 0.83.
2. Code kích hoạt Repair ghi đè (build_clean_dataframe từ raw JSON lại) → **Quality Gate phục hồi cờ True** → RAG Hit Rate phục hồi tuyệt đối 100%.

**Corruption nào ảnh hưởng rõ nhất và vì sao?**
Lỗi "Blank summary" (cố tình làm rỗng 5 dòng bằng Pandas `loc`) ảnh hưởng nghiêm trọng nhất. Vì bản chất RAG dựa trên Vector Embedding, nên việc mất đi văn bản khiến Vector DB tìm sai, dẫn tới không có Context cung cấp cho LLM (Retrieval Hit = False).

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Việc sử dụng công cụ Data Quality Validation chuyên nghiệp như `Great Expectations` (thay vì viết if-else thủ công) đem lại hiệu năng mạnh mẽ để bắt lỗi dữ liệu.
2. Thiết kế đường ống (Pipeline Orchestration) cần tôn trọng nguyên tắc **Idempotent** (có thể chạy đi chạy lại mà không hỏng). Bằng chứng là bước Repair chỉ đơn giản là Fetch raw records và Index lại, hệ thống sửa chữa mà không sập.
3. Việc gọi API LLM (như Gemini) luôn tiềm ẩn rủi ro Rate Limit hoặc Network Timeout. Các cơ chế Retry/Backoff là bắt buộc.

### Nếu có thêm thời gian

Mình muốn nâng cấp `reporting.py` để không chỉ lưu Markdown vào ổ đĩa, mà gửi tự động Markdown này lên một kênh Slack hoặc Telegram (thông qua Webhook). Như vậy khi hệ thống chạy cronjob ban đêm mà Quality check = False, Data Engineer sẽ nhận được cảnh báo real-time qua điện thoại để xử lý ngay.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Thu Trang
**Ngày xác nhận:** 2026-09-25
