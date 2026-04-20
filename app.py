# ===== app.py =====
from flask import Flask
from auth import auth_bp
from database import init_db

app = Flask(__name__)
app.secret_key = "super-secret-key"

# register blueprint
app.register_blueprint(auth_bp)

# init database
init_db()

from datetime import datetime
import pytz


@app.template_filter('thai_time')
def thai_time_filter(value):
    if not value:
        return "-"

    utc = pytz.utc
    thai = pytz.timezone("Asia/Bangkok")

    # แปลง string → datetime
    dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

    # บอกว่าเป็น UTC
    dt = utc.localize(dt)

    # แปลงเป็นเวลาไทย
    dt_th = dt.astimezone(thai)

    return dt_th.strftime("%Y-%m-%d %H:%M:%S")



if __name__ == "__main__":
    app.run(debug=True)
