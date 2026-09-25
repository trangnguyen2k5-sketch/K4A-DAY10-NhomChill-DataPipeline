# Báo cáo kết quả chung của Nhóm

**Tên Nhóm:** NhomChill
**Số lượng thành viên:** 2

## 1. Phân công công việc (Role & Responsibility)
1. **Nguyễn Tiến Đạt** Source owner (`crossref.py`); Data model & evaluation-set owner (`cleaning.py`, `testset.py`)
2. **Nguyễn Thu Trang** Observability owner (`quality.py`, `reporting.py`); Corruption & integration owner (`corruption.py`, `phase1.py`, `corruption_flow.py`)

## 2. Kết quả đạt được (End-to-End Pipeline)

Nhóm đã hiện thực hóa thành công một Data/AI Pipeline 7 lớp tiêu chuẩn theo yêu cầu dự án. Toàn bộ mã nguồn đã được gắn kết, có thể chạy mượt mà từ đầu đến cuối chỉ với 2 lệnh:

- `python src/pipelines/phase1.py`
- `python src/pipelines/corruption_flow.py`

### 2.1 Quá trình từ Raw đến Vector Index (Phase 1)
- Lấy thành công dữ liệu từ Crossref API thông qua hệ thống có Retry và Offline Backup, xuất ra `data/raw/raw_records.json`.
- Tiền xử lý (Clean/Transform) để tạo nên bảng dữ liệu chuẩn chứa metadata và trường gộp `text_for_embedding` chất lượng cao, xuất ra `data/clean/papers_clean.csv`.
- Embedding bộ dữ liệu clean và cất giữ Index an toàn vào CSDL Vector ChromaDB.
- Khởi tạo Data Quality Gate sử dụng Great Expectations để chặn lỗi độ dài, lỗi Null và kiểm tra độ cũ/mới của tin (Freshness). Phase 1 ghi nhận hệ thống PASS với các chỉ số Retrieval xuất sắc (Ghi tại file Markdown Phase 1).

### 2.2 Quá trình Mô phỏng đứt gãy và Tự phục hồi (Phase 2 - Corruption Flow)
- Nhóm đã kích hoạt cố ý kịch bản làm hỏng dữ liệu: Xóa, bỏ trống (blank) văn bản, nhân đôi (duplicate) và làm cũ (staleness) tin bài.
- Quality Gates chớp tắt: Log hệ thống lập tức bắt được các bất thường qua báo cáo `corrupted_quality_report.json`.
- Sự suy giảm RAG: Chấm điểm qua tập Evaluation tự động do LLM Judge (Mock) thực hiện cho thấy Hit rate và độ chính xác F1 rớt thê thảm.
- Phục hồi an toàn (Idempotent repair): Pipeline tái nạp dữ liệu sạch, Indexing lại từ đầu, và LLM Judge xác nhận phục hồi toàn bộ Metrics về như Baseline ban đầu.

## 3. Bài học rút ra (Lesson Learned)
- Không bao giờ được tin tưởng 100% vào nguồn dữ liệu API hay CSDL (luôn có rác, null, thay đổi schema). Bước Validation / Observability không phải là tính năng "Nice-to-have" mà là "Must-have" cho mọi hệ thống RAG thực chiến.
- Việc chia Code base thành các Module độc lập (Source, Clean, Index, Eval, Observability) cùng với Contract rõ ràng (Dataclass, Schema) giúp 4 thành viên trong nhóm code song song mà không bị giẫm chân lên nhau.
- LLM As A Judge là một khái niệm tuyệt vời giúp đo lường định lượng chính xác chất lượng trả lời thay vì dùng mắt đọc thủ công.
