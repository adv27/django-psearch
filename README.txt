Yêu cầu pip (python), npm (node), mongodb

1) Cài bower => cài đặt thư viện css và js
-> npm install bower -g
Trỏ vào thư mục project (có file bower.json)
-> bower install
2) Cài các thư việc cho python (sử dụng venv)
-> virtualenv venv
-> venv\Scripts\activate
-> pip install -r requirements.txt
3) Mongo
-> mongod
4) Run server
-> python manage.py runserver

# Hướng dẫn sử dụng hệ thống Recommend
- Xây dựng model
-> python recommend\LDAModel_English.py

# Chú thích các option trong recommend\settings.py
+) NUM_TOPICS => số lượng topics
+) DATA_FIELDS => các trường dữ liệu của patent sẽ được đưa vào để làm data

# Chú thích các option trong patentsearch\recommendation_settings.py
+) NUMBER_OF_RECOMMENDATION => số lượng gợi ý sẽ hiển thị ra ở front-end
+) USE_USER_HISTORY => có sử dụng lịch sử xem của người dùng cho việc gợi ý
+) N_RECENTLY_VIEWED => số lượng patent được xem gần đây nhất (có tính cả patent đang xem) để làm dữ liệu đầu vào cho việc gợi ý