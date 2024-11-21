import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the CSV file
file_path = 'Activities.csv'
data = pd.read_csv(file_path)

# Convert 'Dato' to datetime format
data['Dato'] = pd.to_datetime(data['Dato'])

# Filter out the necessary columns
heart_rate = data['Gjennomsnittlig puls']
pace = data['Gjennomsnittlig tempo']
dates = data['Dato']

# Convert pace from "9:04" format to decimal
pace = pace.apply(lambda x: int(x.split(':')[0]) + int(x.split(':')[1])/60)

# Calculate moving averages (using a 5-point window)
window_size = 5
pace_avg = pace.rolling(window=window_size, center=True).mean()
heart_rate_avg = heart_rate.rolling(window=window_size, center=True).mean()

# Create a plot
fig, ax1 = plt.subplots(figsize=(14, 7))

# Plotting pace and pace average
ax1.plot(dates, pace, label='Average Pace', color='blue', alpha=0.3)
ax1.plot(dates, pace_avg, label='Pace Trend (5-run avg)', color='blue', linewidth=2)
ax1.set_title('Pace and Heart Rate Over Time')
ax1.set_xlabel('Date')
ax1.set_ylabel('Pace (min/km)', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')
ax1.legend(loc='upper left')
ax1.grid(True)
ax1.invert_yaxis()  # Invert the y-axis for pace

# Create a secondary y-axis for heart rate
ax2 = ax1.twinx()
ax2.plot(dates, heart_rate, label='Average Heart Rate', color='red', alpha=0.3)
ax2.plot(dates, heart_rate_avg, label='Heart Rate Trend (5-run avg)', color='red', linewidth=2)
ax2.set_ylabel('Heart Rate (bpm)', color='red')
ax2.tick_params(axis='y', labelcolor='red')
ax2.legend(loc='upper right')

# Improve layout and show plot
fig.tight_layout()
plt.show()