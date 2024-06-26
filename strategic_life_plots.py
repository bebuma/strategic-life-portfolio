import os
import re
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
from adjustText import adjust_text

# Define output folder
absolute_path = os.path.abspath(__file__)
output_folder = os.path.join(os.path.dirname(absolute_path), "output")
os.makedirs(output_folder, exist_ok=True)

def print_welcome_message():
    """Print the welcome message and today's date."""
    date = datetime.today().strftime("%d/%m/%Y")
    print("\nWelcome to Strategic Life Portfolio!")
    print(f"\nToday is {date}")

def get_user_name():
    """Get the user's name or return a default message if input is invalid."""
    try:
        name = str(input(f"\nEnter your name: "))
    except ValueError:
        name = "Anonymous"
    return name

def define_slas_and_colors():
    """Define strategic life areas (SLAs) and their colors."""
    return {
            "Relationships": "#ff8080",
            "Body, mind, & spirituality": "#8080ff",
            "Community & society": "#80c080",
            "Job, learning, & finances": "#ffff80",
            "Interests & entertainment": "#c080c0",
            "Personal care": "#bfbfbf",
        }

def define_metrics_info():
    """Define metrics and their corresponding SLAs."""
    return {
        "Significant other": "Relationships",
        "Family": "Relationships",
        "Friendship": "Relationships",
        "Physical health/sports": "Body, mind, & spirituality",
        "Spirituality/faith": "Body, mind, & spirituality",
        "Mental health/mindfulness": "Body, mind, & spirituality",
        "Community/citizenship": "Community & society",
        "Societal engagement": "Community & society",
        "Job/career": "Job, learning, & finances",
        "Education/learning": "Job, learning, & finances",
        "Finances": "Job, learning, & finances",
        "Hobbies/interests": "Interests & entertainment",
        "Online entertainment": "Interests & entertainment",
        "Offline entertainment": "Interests & entertainment",
        "Physiological needs": "Personal care",
        "Activities of daily living": "Personal care",
    }

def convert_to_minutes(time_str):
    """Convert a time string (e.g., '2h30m', '1', '30m') to total minutes."""
    total_minutes = 0
    time_str = time_str.lower().strip()

    # Regular expression to match hours and minutes
    pattern = re.compile(r'(?:(\d+)h)?(?:(\d+)m)?')
    match = pattern.fullmatch(time_str)

    if match:
        hours = match.group(1)
        minutes = match.group(2)

        if hours:
            total_minutes += int(hours) * 60
        if minutes:
            total_minutes += int(minutes)
    else:
        # If the string is just a number, treat it as hours
        if time_str.isdigit():
            total_minutes += int(time_str) * 60

    return total_minutes

def input_metrics(metrics_info):
    """Input metrics from the user."""
    entries = []
    current_sla = "NA"
    for metric, sla in metrics_info.items():
        if current_sla != sla:
            current_sla = sla
            print(f"\nStrategic life areas (SLAs) : {sla}")

        importance = get_valid_float_input(
            f"\nEnter the importance of {metric} (0-10): ", 0, 10
        )
        satisfaction = get_valid_float_input(
            f"Enter your satisfaction with {metric} (0-10): ", 0, 10
        )
        time = convert_to_minutes(
            input(f"Enter the time invested (hour) in {metric} (e.g. 1 or 30m or 1h40m): ")
            .strip()
            .lower()
        )

        entries.append(
            {
                "Metric": metric,
                "Importance": importance,
                "Satisfaction": satisfaction,
                "Time": time,
            }
        )
    return entries

def get_valid_float_input(prompt, min_value, max_value):
    """Get a valid float input from the user within a specified range."""
    while True:
        try:
            value = float(input(prompt))
            if min_value <= value <= max_value:
                return value
            else:
                print(f"Please enter a value between {min_value} and {max_value}.")
        except ValueError:
            print("Invalid input. Please enter a numerical value.")

def adjust_text_labels(ax, data):
    """Adjust text labels to avoid overlapping."""
    texts = []
    for i, row in data.iterrows():
        text_x = row["Satisfaction"] + 0.5 if row["Satisfaction"] <= 9.5 else row["Satisfaction"] - 0.5
        text_y = row["Importance"] + 0.5 if row["Importance"] <= 9.5 else row["Importance"] - 0.5
        text = ax.text(
            text_x,
            text_y,
            row["Metric"],
            fontsize=9,
            ha="left",
            va="bottom",
            color="black",
        )
        texts.append(text)
    return texts


def plot_metrics(data, sla_colors, metrics_info, name, output_folder="."):
    """Plot the metrics in a 2x2 matrix."""
    fig, ax = plt.subplots(figsize=(8, 8))  # Adjusted the figure size to be twice as large

    # Sort data by 'Time' in ascending order
    data = data.sort_values(by='Time', ascending=False)

    texts = []
    for i, row in data.iterrows():
        color = sla_colors[metrics_info[row["Metric"]]]
        size = (row["Time"] / (7 * 24 * 60)) * 50000  # Convert time to percentage of the week and scale for visibility
        ax.scatter(
            row["Satisfaction"],
            row["Importance"],
            s=size,
            color=color,
            alpha=1,
            edgecolors="w",
            linewidth=0.5,
        )
        # Adjust text placement to avoid overlap
        text_x = row["Satisfaction"] + 0.5 if row["Satisfaction"] <= 9.5 else row["Satisfaction"] - 0.5
        text_y = row["Importance"] + 0.5 if row["Importance"] <= 9.5 else row["Importance"] - 0.5
        ax.plot([row["Satisfaction"], text_x],
                [row["Importance"], text_y],
                color='gray', linestyle='--', linewidth=0.5)
        texts.append(ax.text(text_x, text_y, row["Metric"], fontsize=9))

    # Adjust text labels to avoid overlap
    adjust_text(texts, ax=ax) #, arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))

    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_xlabel("Satisfaction")
    ax.set_ylabel("Importance")
    ax.set_title("Strategic Life Portfolio")
    plt.grid(True)
    plt.axvline(x=5, color="gray", linestyle="--")
    plt.axhline(y=5, color="gray", linestyle="--")
    
    plt.show()
    fig.savefig(os.path.join(output_folder, name))


def main():
    print_welcome_message()
    ##########
    name = "Anonymous"
    entries = [
                    {"Metric": "Significant other", "Importance": 8.0, "Satisfaction": 3.0, "Time": 840.0},
                    {"Metric": "Family", "Importance": 9.0, "Satisfaction": 4.0, "Time": 420.0},
                    {"Metric": "Friendship", "Importance": 7.0, "Satisfaction": 3.0, "Time": 210.0},
                    {"Metric": "Physical health/sports", "Importance": 5.0, "Satisfaction": 5.0, "Time": 420.0},
                    {"Metric": "Spirituality/faith", "Importance": 4.0, "Satisfaction": 4.0, "Time": 210.0},
                    {"Metric": "Mental health/mindfulness", "Importance": 2.0, "Satisfaction": 6.0, "Time": 45.0},
                    {"Metric": "Community/citizenship", "Importance": 3.0, "Satisfaction": 3.0, "Time": 420.0},
                    {"Metric": "Societal engagement", "Importance": 2.0, "Satisfaction": 2.0, "Time": 210.0},
                    {"Metric": "Job/career", "Importance": 8.0, "Satisfaction": 7.0, "Time": 840.0},
                    {"Metric": "Education/learning", "Importance": 7.0, "Satisfaction": 6.0, "Time": 420.0},
                    {"Metric": "Finances", "Importance": 9.0, "Satisfaction": 8.0, "Time": 420.0},
                    {"Metric": "Hobbies/interests", "Importance": 6.0, "Satisfaction": 5.0, "Time": 420.0},
                    {"Metric": "Online entertainment", "Importance": 1.0, "Satisfaction": 4.0, "Time": 840.0},
                    {"Metric": "Offline entertainment", "Importance": 4.0, "Satisfaction": 3.0, "Time": 420.0},
                    {"Metric": "Physiological needs", "Importance": 7.0, "Satisfaction": 2.0, "Time": 420.0},
                    {"Metric": "Activities of daily living", "Importance": 8.0, "Satisfaction": 7.0, "Time": 420.0},
                ]
    ##########
    try:
        name
    except NameError:
        name = get_user_name()
    sla_colors = define_slas_and_colors()
    metrics_info = define_metrics_info()

    data = pd.DataFrame(columns=["Metric", "Importance", "Satisfaction", "Time"])
    
    try:
        entries
    except NameError:
        entries = input_metrics(metrics_info)

    data = pd.DataFrame(entries)

    plot_metrics(data, sla_colors, metrics_info, name, output_folder)
    print("Thank you! :)")

if __name__ == "__main__":
    main()
