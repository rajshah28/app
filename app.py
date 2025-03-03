from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session management
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def save_excel(dataframe, filename="Rated_Query_Evaluation_Sheet.xlsx"):
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    dataframe.to_excel(save_path, index=False)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            session["uploaded_file"] = filepath  # Store file path in session
            df = pd.read_excel(filepath)
            session["columns"] = df.columns.tolist()
            return redirect(url_for("select_columns"))
    return render_template("index.html")

@app.route("/select_columns", methods=["GET", "POST"])
def select_columns():
    if "uploaded_file" not in session:
        return redirect(url_for("index"))
    columns = session.get("columns", [])
    if request.method == "POST":
        session["query_column"] = request.form["query_column"]
        session["response_column"] = request.form["response_column"]
        session["rating_columns"] = request.form.getlist("rating_columns")
        session["current_row"] = 0  # Start at the first row
        session["ratings"] = []  # Initialize empty list for ratings
        return redirect(url_for("rate"))
    return render_template("select_columns.html", columns=columns)

@app.route("/rate", methods=["GET", "POST"])
def rate():
    if "uploaded_file" not in session or "query_column" not in session:
        return redirect(url_for("index"))

    df = pd.read_excel(session["uploaded_file"])
    row_idx = session.get("current_row", 0)
    
    if row_idx >= len(df):  # If all rows are rated
        return redirect(url_for("submit_ratings"))

    query = df.at[row_idx, session["query_column"]]
    response = df.at[row_idx, session["response_column"]]
    rating_columns = session["rating_columns"]

    if request.method == "POST":
        ratings = {col: request.form[col] for col in rating_columns}
        ratings.update({"Query": query, "Response": response})
        session["ratings"].append(ratings)
        session["current_row"] += 1  # Move to the next row

        if session["current_row"] >= len(df):  # If last row is rated
            return redirect(url_for("submit_ratings"))

        return redirect(url_for("rate"))  # Load the next row

    return render_template("rate.html", 
                           query=query, 
                           response=response, 
                           rating_columns=rating_columns, 
                           row_idx=row_idx + 1, 
                           total_rows=len(df))

@app.route("/submit_ratings", methods=["GET", "POST"])
def submit_ratings():
    if request.method == "POST":
        df_rated = pd.DataFrame(session["ratings"])
        save_excel(df_rated)
        session.clear()  # Clear session after submission
        return "Ratings saved successfully! <a href='/'>Upload another file</a>"
    return redirect(url_for("index"))




if __name__ == "__main__":
    app.run(debug=True)
