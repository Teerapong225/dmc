from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# โหลดไฟล์ Excel
file_path = "C:/Users/acer/Desktop/startbootstrap-heroic-features-master/dist/data/food.xlsx"
df = pd.read_excel(file_path, sheet_name="Sheet6", skiprows=2,
                   names=["Business Date", "Country", "Major Group", "Menu Item Name", "Count"])

# แปลงประเภทข้อมูลให้ถูกต้อง
df["Business Date"] = pd.to_datetime(df["Business Date"], errors="coerce")
df["Major Group"] = df["Major Group"].fillna("Unknown")  # แทนค่า NaN
df["Count"] = pd.to_numeric(df["Count"], errors="coerce").fillna(
    0)  # แปลง Count เป็นตัวเลข


@app.route("/get_data", methods=["GET"])
def get_data():
    try:
        # รับค่าจาก Query Parameters
        country = request.args.get("country", "").strip()
        top_rank = request.args.get("toprank", "").strip()
        food_type = request.args.get("foodType", "").strip()
        date_from_str = request.args.get("dateFrom", "").strip()
        date_to_str = request.args.get("dateTo", "").strip()

        if country == "United Kingdom":
            country = "Great Britain"

        if not country or not date_from_str or not date_to_str:
            return jsonify({"error": "Missing required parameters"}), 400
        
        try:
            top_rank = int(top_rank) if top_rank.isdigit() else 100

        except ValueError:
            return jsonify({"error": "Invalid value for topRank"}), 400

        # แปลงวันที่
        date_from = pd.to_datetime(
            date_from_str, format="%d/%m/%Y", errors="coerce")
        date_to = pd.to_datetime(
            date_to_str, format="%d/%m/%Y", errors="coerce")

        if pd.isna(date_from) or pd.isna(date_to):
            return jsonify({"error": "Invalid date format. Use DD/MM/YYYY"}), 400

        if date_from > date_to:
            return jsonify({"error": "dateFrom must be earlier than or equal to dateTo"}), 400

        # กรองข้อมูลตามวันที่และประเทศ
        filtered_df = df[(df["Business Date"] >= date_from) & (
            df["Business Date"] <= date_to) & (df["Country"] == country)]

        # กรณี foodType ไม่ใช่ "All" ให้กรองเฉพาะประเภทนั้น
        if food_type and food_type != "All":
            # กรณีที่กรองโดย Major Group (food_type != "All")
            filtered_df = filtered_df[filtered_df["Major Group"] == food_type]

            #ถ้าหลังจากกรองแล้วไม่มีข้อมูล ให้คืน []
            if filtered_df.empty:
                return jsonify([])

            # รวม Count ตาม "Major Group" และ "Menu Item Name"
            grouped_df = (filtered_df.groupby(["Major Group", "Menu Item Name"])["Count"]
                        .sum()
                        .reset_index()
                        .sort_values(by="Count", ascending=False))

            # แสดง 10 อันดับแรก หรือเท่าที่มี
            top_items = grouped_df.head(min(top_rank, len(grouped_df)))

            # จัดโครงสร้าง JSON ให้เป็นแบบที่ต้องการ
            result = [{
                "Major Group": food_type,
                "Menu Item Name": top_items.to_dict(orient="records")
            }]

        else:
            #กรณี foodType = "All" ให้แสดง 10 อันดับแรกของแต่ละ foodType
            result = []
            for food_type, food_type_df in filtered_df.groupby("Major Group"):  # ใช้ Major Group สำหรับกรุ๊ปตาม foodType
                top_items = (food_type_df.groupby("Menu Item Name")["Count"]
                            .sum()
                            .reset_index()
                            .sort_values(by="Count", ascending=False)
                            .head(min(top_rank, len(food_type_df))))  # เลือก 10 อันดับแรกหรือตามจำนวนที่มี

                # เพิ่มข้อมูลในโครงสร้าง JSON
                result.append({
                    "foodType": food_type,  # เพิ่มชื่อ foodType
                    "Menu Item Name": top_items.to_dict(orient="records")
                 })

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
