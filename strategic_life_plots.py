import matplotlib.pyplot as plt
import pandas as pd

# Define the strategic life areas (SLAs) and their colors
sla_colors = {
    "Relationships": "red",
    "Body, mind, & spirituality": "blue",
    "Community & society": "green",
    "Job, learning, & finances": "yellow",
    "Interests & entertainment": "purple",
    "Personal care": "grey"
}

# Define the metrics and their corresponding SLAs
metrics_info = {
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
    "Activities of daily living": "Personal care"
}

# Create an empty DataFrame to store the data
data = pd.DataFrame(columns=["Metric", "Importance", "Satisfaction", "Time"])

def input_metrics():
    """Function to input metrics from the user."""
    entries = []
    sla = "NA"
    for metric in metrics_info.keys():
        if sla != metrics_info[metric]:
            sla = metrics_info[metric]
            print(f"\nStrategic life areas (SLAs) : {sla}\n")
        try:
            importance = float(input(f"Enter the importance of {metric} (0-10): "))
        except ValueError:
            importance = 0
        try:
            satisfaction = float(input(f"Enter your satisfaction with {metric} (0-10): "))
        except ValueError:
            satisfaction = 0
        try:
            time_input = input(f"Enter the time invested in {metric} (e.g., '2h' for 2 hours or '30m' for 30 minutes): ").strip().lower()
            if 'h' in time_input:
                time = float(time_input.replace('h', '')) * 60  # Convert hours to minutes
            elif 'm' in time_input:
                time = float(time_input.replace('m', ''))
            else:
                time = 0
        except ValueError:
            time = 0
        entries.append({"Metric": metric, "Importance": importance, "Satisfaction": satisfaction, "Time": time})
    return entries

def plot_metrics(data):
    """Function to plot the metrics in a 2x2 matrix."""
    fig, ax = plt.subplots()

    for i, row in data.iterrows():
        color = sla_colors[metrics_info[row["Metric"]]]
        size = (row["Time"] / (7 * 24 * 60)) * 10000  # Convert time to percentage of the week and scale for visibility
        ax.scatter(row["Satisfaction"], row["Importance"], s=size, color=color, label=row["Metric"], alpha=0.6, edgecolors="w", linewidth=0.5)
        ax.text(row["Satisfaction"], row["Importance"], row["Metric"], fontsize=9, ha="center", va="center", color="black")

    # Remove duplicate labels in the legend
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(1.05, 1), loc="upper left")

    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_xlabel("Satisfaction")
    ax.set_ylabel("Importance")
    ax.set_title("Strategic Life Portfolio")
    plt.grid(True)
    plt.axvline(x=5, color="gray", linestyle="--")
    plt.axhline(y=5, color="gray", linestyle="--")
    plt.show()

def main():
    while True:
        entries = input_metrics()
        for entry in entries:
            data.loc[len(data)] = entry
        plot_metrics(data)
        cont = input("Do you want to add another entry? (yes/no): ")
        if cont.lower() != "yes":
            break

if __name__ == "__main__":
    main()
