from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend for Flask
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = 'change_this_secret_key'


def create_plot_and_analysis(df, x_col, y_col):
    """Creates a plot and performs basic analysis text for the selected columns."""
    # 1. Create Plot
    fig, ax = plt.subplots()
    ax.plot(df[x_col], df[y_col], marker='o')
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(f'{y_col} vs {x_col}')

    # Save plot to PNG in memory
    img = io.BytesIO()
    plt.tight_layout()
    fig.savefig(img, format='png')
    plt.close(fig)
    img.seek(0)
    plot_png = base64.b64encode(img.getvalue()).decode('utf8')

    # 2. Analysis - Basic Descriptive Stats
    series = df[y_col].dropna()
    desc = series.describe()

    # Simple text interpretation
    analysis_text = []
    analysis_text.append(f"There are {int(desc['count'])} data points.")
    analysis_text.append(
        f"The mean of {y_col} is {desc['mean']:.2f}, "
        f"with a standard deviation of {desc['std']:.2f}."
    )
    analysis_text.append(
        f"The minimum value is {desc['min']:.2f} and the maximum value is {desc['max']:.2f}."
    )
    analysis_text.append(f"The median value is {desc['50%']:.2f}.")

    # Trend detection (very simple)
    if len(series) >= 2:
        if series.iloc[-1] > series.iloc[0]:
            trend = "increasing overall"
            analysis_text.append(
                f"There is an increasing trend in {y_col} over the range of {x_col}."
            )
        elif series.iloc[-1] < series.iloc[0]:
            trend = "decreasing overall"
            analysis_text.append(
                f"There is a decreasing trend in {y_col} over the range of {x_col}."
            )
        else:
            trend = "roughly constant overall"
            analysis_text.append(
                f"There is no significant trend in {y_col} over the range of {x_col}."
            )

        analysis_text.append(
            f"From the first point ({series.iloc[0]:.2f}) to the last ({series.iloc[-1]:.2f}), "
            f"{y_col} is {trend}."
        )
    else:
        analysis_text.append(
            "There are not enough data points to clearly determine a trend."
        )

    return plot_png, desc.to_dict(), analysis_text


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part in the request.")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("No file selected.")
            return redirect(request.url)

        try:
            df = pd.read_csv(file)
        except Exception as e:
            flash(f"Error reading CSV: {e}")
            return redirect(request.url)

        # Allow user to pick numeric columns; do it on /result
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if len(numeric_cols) < 1:
            flash("No numeric columns found in the file.")
            return redirect(request.url)

        # For simplicity, auto-select first two numeric columns if available
        x_col = numeric_cols[0]
        y_col = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]

        plot_png, stats, analysis_text = create_plot_and_analysis(df, x_col, y_col)

        return render_template(
            "result.html",
            columns=numeric_cols,
            x_col=x_col,
            y_col=y_col,
            stats=stats,
            analysis_text=analysis_text,
            plot_png=plot_png,
        )

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
