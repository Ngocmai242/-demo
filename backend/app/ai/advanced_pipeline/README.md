# AuraFit Advanced AI Pipeline

Đây là hệ thống phân tích hình thể nâng cao sử dụng mô hình 3D (SMPL), Deep Learning (EfficientNet-B3) và GenAI (Gemma-3).

## 1. Cấu trúc thư mục
- `smpl_engine.py`: Tái tạo 3D và đo kích thước.
- `classifier.py`: Phân loại giới tính và dáng người.
- `llm_advisor.py`: Gợi ý phong cách bằng AI.
- `pipeline.py`: API chính để chạy toàn bộ quy trình.
- `models/`: Thư mục chứa các file mô hình (Cần tải về riêng).

## 2. Hướng dẫn tải Model Files (BẮT BUỘC)

### Bước A: SMPL 3D Models
1. Truy cập [SMPL Website](https://smpl.is.tue.mpg.de/).
2. Đăng ký tài khoản (dùng email học thuật nếu có).
3. Tải gói **SMPL for Python** (thường có tên `SMPL_python_v.1.x.x.zip`).
4. Giải nén, tìm các file:
   - `basicModel_f_lbs_10_207_0_v1.0.0.pkl` -> Đổi tên thành `SMPL_FEMALE.pkl`
   - `basicModel_m_lbs_10_207_0_v1.0.0.pkl` -> Đổi tên thành `SMPL_MALE.pkl`
5. Chép 2 file này vào thư mục `backend/app/ai/advanced_pipeline/models/`.

### Bước B: EfficientNet Weights
Mặc định code sẽ tự tải bản pre-trained trên ImageNet từ `timm`. 
Để đạt độ chính xác >90% trên dáng người, bạn cần fine-tune với dataset (ví dụ DeepFashion2) và lưu file vào:
- `backend/app/ai/advanced_pipeline/models/efficientnet_body.pth`

### Bước C: LLM (Gemma-3)
Code sử dụng thư viện `transformers` để tự động tải mô hình từ Hugging Face.
Bạn cần có tài khoản Hugging Face và đã chấp nhận điều khoản sử dụng mô hình Gemma của Google.
Sử dụng lệnh: `huggingface-cli login` và nhập Token của bạn.

## 3. Cài đặt môi trường
Mở terminal tại thư mục này và chạy:
```bash
pip install -r requirements.txt
```

## 4. Khởi chạy API
```bash
python pipeline.py
```
API sẽ lắng nghe tại `http://localhost:5000/api/ai/advanced/analyze`.

## 5. Sử dụng
Gửi lệnh POST với ảnh người dùng:
```bash
curl -X POST -F "image=@photo.jpg" http://localhost:5000/api/ai/advanced/analyze
```
