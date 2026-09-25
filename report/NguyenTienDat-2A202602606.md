# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                                                                      |
| --------------- | ----------------------------------------------------------------------------- |
| Họ và tên       | Nguyễn Tiến Đạt                                                               |
| MSSV            | 2A202602606                                                                   |
| Khóa/Lớp        | K4                                                                            |
| Tên nhóm        | NhomChill                                                                     |
| Vai trò chính   | Pipeline Lead & Data Foundation Owner                                         |
| Repository      | <https://github.com/trangnguyen2k5-sketch/K4-L3-DAY10-NhomChill-DataPipeline> |
| Ngày hoàn thành | 2026-09-25                                                                    |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách          | Input nhận vào                                      | Output bàn giao                                              | Trạng thái |
| ------------------ | --------------------------- | --------------------------------------------------- | ------------------------------------------------------------ | ---------- |
| Thu thập dữ liệu   | `src/ingestion/crossref.py` | Cấu hình query/filter từ `settings`                 | Bản raw JSON (`crossref_records.json`) và list `PaperRecord` | Hoàn thành |
| Làm sạch dữ liệu   | `src/ingestion/cleaning.py` | Danh sách `PaperRecord`                             | DataFrame sạch (`papers_clean.csv`, `papers_clean.json`)     | Hoàn thành |
| Pipeline Phase 1   | `src/pipelines/phase1.py`   | Các hàm thành phần từ ingestion, retrieval, quality | Luồng chạy Baseline (Bước 1->4)                              | Một phần   |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                | Thành viên/module được hỗ trợ | Kết quả                                                        |
| ------------------------ | ----------------------------- | -------------------------------------------------------------- |
| Viết luồng Orchestration | Thành viên 2                  | Chuẩn bị sẵn placeholder (TODO) trong `phase1.py` để tích hợp. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện       | File/hàm/artifact liên quan | Kết quả bàn giao                 | Cách xác minh                                                                  |
| --------------------------- | --------------------------- | -------------------------------- | ------------------------------------------------------------------------------ |
| Cào & bóc tách metadata     | `src/ingestion/crossref.py` | `data/raw/crossref_records.json` | Chạy `python script/run_phase1.py` (In ra 'Fetched 24 records')                |
| Chuẩn hóa Data & Embed text | `src/ingestion/cleaning.py` | `data/clean/papers_clean.csv`    | Chạy `python script/run_phase1.py` (In ra 'Cleaned dataframe shape: (24, 16)') |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Tạo ra file `data/clean/papers_clean.csv` với 16 trường dữ liệu chuẩn chỉnh, bao gồm cột quan trọng `text_for_embedding` (được ghép từ tiêu đề, tóm tắt, tác giả, chuyên ngành) phục vụ trực tiếp cho mô hình sinh Vector nhúng của Thành viên 3.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Hệ thống RAG cần dữ liệu văn bản sạch và giàu ngữ cảnh. Tuy nhiên dữ liệu từ API Crossref chứa nhiều thẻ rác (như XML `<jats:p>`), cấu trúc lồng nhau (tác giả, ngày xuất bản) và nhiều bản ghi thiếu tóm tắt hoặc bị trùng lặp. Vấn đề là phải "cứu hộ" (preserve) bản gốc và biến nó thành một DataFrame phẳng, sạch, sẵn sàng nhúng Vector.

### Cách triển khai

1. **Ingestion**: Gửi request tới Crossref API, sử dụng tính năng try-catch để dự phòng (fallback) đọc file snapshot nếu mạng rớt. Parse các trường JSON phức tạp (như mảng `date-parts`) thành định dạng ISO 8601.
2. **Cleaning**: Sử dụng thư viện `pandas` để:
   - Dùng `.replace()` và `.strip()` để làm sạch chuỗi.
   - Ép kiểu bằng `pd.to_datetime()` và tính số tuổi `age_days`.
   - Dùng toán tử chuỗi ghép cột `text_for_embedding`.
   - Dùng `.drop_duplicates(subset=['paper_id'])` và lọc `summary_chars >= 30` để loại rác.

### Input, output và contract

| Thành phần              | Mô tả                                                                       |
| ----------------------- | --------------------------------------------------------------------------- |
| Input                   | Raw JSON API response hoặc file snapshot offline                            |
| Output                  | DataFrame Pandas chứa `paper_id`, `title`, `text_for_embedding`, `age_days` |
| Module phụ thuộc        | API Crossref, `core.config.Settings`                                        |
| Module sử dụng output   | `retrieval.index` (TV3), `observability.quality` (TV4)                      |
| Điều kiện lỗi cần xử lý | Mất kết nối mạng (Timeout) -> Fallback đọc từ JSON local.                   |

### Cách xác minh

```bash
python script/run_phase1.py
```

- **Kết quả mong đợi:** Tải 24 bài báo và làm sạch mà không gặp lỗi.
- **Kết quả thực tế:** Màn hình in ra log quá trình từ bước 1 tới bước 4. Số record là 24, số cột sau clean là 16.
- **Artifact/log:** Tạo ra `data/clean/papers_clean.csv`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Xử lý sự cố mạng bị lỗi hoặc API trả về HTTP 429 Too Many Requests trong quá trình Ingestion.
- **Các phương án đã cân nhắc:** (1) Dừng chương trình báo lỗi. (2) Tự động Retry vài lần rồi dừng. (3) Fallback đọc từ bản snapshot offline (Raw Preservation).
- **Phương án đã chọn:** Phương án (3) - Fallback đọc từ file snapshot `crossref_response.json` đã lưu sẵn nếu request thất bại.
- **Lý do:** Tăng tính ổn định của Pipeline (Robustness). Dữ liệu RAG Pipeline không được chết ngang chỉ vì một API bên ngoài sập. Việc lưu bản gốc cũng giúp Data Engineer debug lại lỗi Data Cleaning sau này.
- **Bằng chứng quyết định phù hợp:** Chạy code không cần bật mạng máy tính, Pipeline vẫn ra được `papers_clean.csv` dựa vào file local JSON.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ModuleNotFoundError: No module named 'core'` khi chạy thử script.
- **Lệnh hoặc bước tái hiện:** Chạy lệnh `python -c "from core.config import load_settings..."`
- **Nguyên nhân gốc:** Trình thông dịch Python không nhận diện thư mục `src/` như một package do chưa cài đặt dự án ở chế độ "editable" vào môi trường ảo, hoặc chạy lệch môi trường.
- **Cách xử lý:** Chạy lệnh `python -m pip install -e .` tại thư mục gốc để liên kết `src/` vào `PYTHONPATH` của môi trường hiện tại.
- **Cách xác minh sau khi sửa:** Chạy lại script trên không còn bị văng exception.
- **Điều học được:** Việc tổ chức package trong thư mục `src/` đòi hỏi cấu hình setup đàng hoàng thay vì gọi script trực tiếp lộn xộn.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Dữ liệu thô từ Crossref API (JSON) -> Lọc và chuẩn hóa (thành list `PaperRecord`) -> Đưa vào DataFrame Pandas để ghép văn bản (`text_for_embedding`) -> Chạy qua Quality Gate (Great Expectations) -> Gửi vào MiniLM để băm thành Vector -> Lưu vào ChromaDB theo batch.
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Dùng để so khớp: câu trả lời của LLM có khớp với `ground_truth` không (Token F1/Judge), và DB có trích xuất đúng tài liệu chứa `ground_truth_doc_ids` hay không (Hit Rate).
3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   Quality checks kiểm tra cấu trúc/dữ liệu hỏng (VD: title rỗng, bị trùng lặp, summary quá ngắn). Freshness monitoring đánh giá "độ tuổi" (age\_days) để cảnh báo bài báo cũ kỹ, không hợp thời đại.
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Để đảm bảo tính công bằng (cùng một cái cân, cùng một đề thi) giúp so sánh độ chính xác của Agent bị giảm bao nhiêu khi gặp data xấu và phục hồi thế nào.
5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Dựa trên artifact là file báo cáo 3 trạng thái và metric khi các chỉ số như `retrieval_hit_rate` và `mean_token_f1` ở pha Repaired phải bằng chính xác với pha Baseline ban đầu.

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

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Dữ liệu vào thế nào thì trí tuệ nhân tạo ra thế nấy. 60-80% công sức nằm ở việc làm sạch và định tuyến pipeline chứ không phải tuning Model.
2. "Bảo hiểm" dữ liệu (luôn lưu bản Raw) là cách thiết kế an toàn nhất để đảm bảo Idempotent Repair (chạy sửa sai nhiều lần không hỏng).
3. Đóng gói đoạn text đầy đủ ngữ cảnh (`text_for_embedding` chứa cả tác giả, tiêu đề, tóm tắt) mang lại khả năng tìm kiếm tốt hơn nhiều so với chỉ nhúng (embed) nội dung rỗng.

### Nếu có thêm thời gian

Tôi sẽ viết thêm module Async (bất đồng bộ) bằng `aiohttp` ở bước Ingestion để nếu phải cào hàng vạn bài báo khoa học thì thời gian kéo API sẽ giảm xuống đáng kể so với việc chạy vòng lặp tuần tự.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- Báo cáo không chứa `.env`, API key, token hoặc secret.
- Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Tiến Đạt
**Ngày xác nhận:** 2026-09-25
