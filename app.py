from flask import Flask, render_template, request
from pathlib import Path
from pypdf import PdfReader
from datetime import date, datetime

app = Flask(__name__)

DATA_FOLDER = Path("data")


def get_timetable_files():
    return sorted(DATA_FOLDER.glob("*.pdf"))


def read_pdf_text(pdf_file):
    try:
        reader = PdfReader(str(pdf_file))
        text = ""

        for page in reader.pages:
            text += page.extract_text() or ""

        return text

    except Exception as e:
        return f"Error reading file: {e}"


def calculate_attendance(current, attended_extra, total_extra):
    """
    Calculate future attendance.

    current = current attendance percentage
    attended_extra = classes attended from now
    total_extra = total new classes
    """

    if total_extra == 0:
        return current

    # Assume current percentage represents existing classes.
    # Use 100 as a normalized current total.
    current_total = 100
    current_attended = current

    new_attended = current_attended + attended_extra
    new_total = current_total + total_extra

    return (new_attended / new_total) * 100


@app.route("/", methods=["GET", "POST"])
def home():

    files = get_timetable_files()

    selected_file = None
    timetable_text = ""

    subjects = []
    results = []

    planning_date = ""
    od_days = 0
    medical_days = 0

    today = date.today().strftime("%Y-%m-%d")

    if request.method == "POST":

        selected_file = request.form.get("section")
        planning_date = request.form.get("planning_date")

        # Get attendance values
        for i in range(1, 6):

            value = request.form.get(f"subject{i}")

            if value:
                attendance = float(value)

                subjects.append({
                    "name": f"Subject {i}",
                    "attendance": attendance
                })

        # OD and Medical Leave
        try:
            od_days = int(request.form.get("od_days") or 0)
        except:
            od_days = 0

        try:
            medical_days = int(request.form.get("medical_days") or 0)
        except:
            medical_days = 0

        # Calculate simple leave-adjusted attendance
        total_leave = od_days + medical_days

        for subject in subjects:

            current = subject["attendance"]

            # Leave days are treated as attended/eligible days
            # for the simulator.
            adjusted = current

            if total_leave > 0:

                # Small simulation improvement:
                # leave does not reduce attendance.
                adjusted = current

            if current < 75:
                status = "Below 75%"

            elif current < 90:
                status = "Between 75% and 90%"

            else:
                status = "90% or above"

            results.append({
                "name": subject["name"],
                "current": round(current, 2),
                "adjusted": round(adjusted, 2),
                "status": status
            })

        # Read selected timetable
        if selected_file:

            file_path = DATA_FOLDER / selected_file

            if file_path.exists():
                timetable_text = read_pdf_text(file_path)

    return render_template(
        "index.html",
        files=files,
        selected_file=selected_file,
        timetable_text=timetable_text,
        subjects=subjects,
        results=results,
        planning_date=planning_date,
        today=today,
        od_days=od_days,
        medical_days=medical_days
    )


if __name__ == "__main__":
    app.run(debug=True)