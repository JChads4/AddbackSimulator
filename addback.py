import numpy as np
import matplotlib.pyplot as plt
import random
from itertools import cycle

# Define a class for the detector event
class DetectorEvent:
    def __init__(self, crystal, energy, timestamp, position):
        self.crystal = crystal  # Crystal number
        self.energy = energy  # Energy deposited in crystal
        self.timestamp = timestamp  # Timestamp of the event in crystal
        self.position = position  # Position within the crystal's quadrant
        self.used = False  # Flag to indicate if the event has been used in an add-back event

# Generate random detector events
def generate_random_events(num_events, max_energy, max_time):
    events = []
    for _ in range(num_events):
        crystal = random.randint(0, 3)  # Crystal number (0 to 3)
        energy = random.uniform(0, max_energy)  # Energy in keV
        timestamp = random.uniform(0, max_time)  # Timestamp in ns

        # Random position within the crystal's quadrant
        # Define quadrant boundaries
        x_min, x_max = (0, 0.5) if crystal % 2 == 0 else (0.5, 1)
        y_min, y_max = (0.5, 1) if crystal < 2 else (0, 0.5)
        position = (random.uniform(x_min, x_max), random.uniform(y_min, y_max))

        events.append(DetectorEvent(crystal, energy, timestamp, position))
    return events


# Parameters for random event generation
num_events = 100  # Number of events to generate
max_energy = 500.0  # Maximum energy in keV
max_time = 10000.0  # Maximum timestamp in ns

# Generate random events
events = generate_random_events(num_events, max_energy, max_time)

# Time order the events
events.sort(key=lambda x: x.timestamp)

# Define a coincidence window in ns
coincidence_window = 100

# Neighbours dict to map a crystal to its neighbouring ones (excluding diagonals)
neighbours = {
    0: [1, 2],  # 0 is only neighbor to 1 (right) and 2 (below)
    1: [0, 3],  # 1 is only neighbor to 0 (left) and 3 (below)
    2: [0, 3],  # 2 is only neighbor to 0 (above) and 3 (right)
    3: [1, 2]   # 3 is only neighbor to 1 (above) and 2 (left)
}

# Add-back function that combines coincident events and returns the
# summed energy, crystal no. with highest energy, and timestamp of that crystal.

def addback(events, coincidence_window):
    addback_events = []  # List to store add-back events
    n = len(events)
    i = 0

    while i < n:
        current_event = events[i]
        if current_event.used:  # Skip used events
            i += 1
            continue

        combined_energy = np.zeros(4)  # Array to store combined energy per crystal
        highest_energy = current_event.energy
        highest_energy_crystal = current_event.crystal
        highest_energy_timestamp = current_event.timestamp
        crystal_added = set()  # Track crystals already added
        crystal_added.add(current_event.crystal)
        combined_energy[current_event.crystal] += current_event.energy

        coincident_events = [current_event]  # List to store coincident events
        current_event.used = True  # Mark the current event as used

        j = i + 1

        while j < n and events[j].timestamp - current_event.timestamp <= coincidence_window:
            if not events[j].used and events[j].crystal != current_event.crystal and events[j].crystal in neighbours[current_event.crystal]:
                if events[j].crystal not in crystal_added:
                    combined_energy[events[j].crystal] += events[j].energy
                    coincident_events.append(events[j])  # Add to coincident events
                    crystal_added.add(events[j].crystal)
                    events[j].used = True  # Mark the event as used

                    if events[j].energy > highest_energy:
                        highest_energy = events[j].energy
                        highest_energy_crystal = events[j].crystal
                        highest_energy_timestamp = events[j].timestamp

            j += 1

        total_energy = combined_energy.sum()
        addback_event = {
            'highest_energy_crystal': highest_energy_crystal,
            'total_energy': total_energy,
            'timestamp': highest_energy_timestamp,
            'coincident_events': coincident_events  # Store coincident events
        }
        addback_events.append(addback_event)

        i = j  # Move to the next set of events

    return addback_events


# Perform addback
addback_events = addback(events, coincidence_window)

# Print the number of add-back events
print(len(addback_events))

# Print the results with details
for idx, event in enumerate(addback_events):
    print(f"Addback Event {idx + 1}:")
    print(f"  Timestamp: {event['timestamp']} ns")
    print(f"  Highest Energy Crystal: {event['highest_energy_crystal']}")
    print(f"  Total Energy: {event['total_energy']} keV")
    print("  Coincident Events:")
    for ce in event['coincident_events']:
        print(f"    Crystal: {ce.crystal}, Energy: {ce.energy} keV, Timestamp: {ce.timestamp} ns")

# Function to plot horizontal and vertical segments for connecting events
def plot_segments(x0, y0, x1, y1, col):
    plt.plot([x0, x1], [y0, y0], col)  # Horizontal segment
    plt.plot([x1, x1], [y0, y1], col)  # Vertical segment

def plot_events(events, addback_events):
    plt.figure(figsize=(12, 12))
    colors = cycle(['red', 'green', 'blue', 'cyan', 'magenta', 'yellow', 'black'])

    # Define quadrant boundaries for each crystal
    quadrant_boundaries = {
        0: (0, 0.5, 0.5, 1),
        1: (0.5, 1, 0.5, 1),
        2: (0, 0.5, 0, 0.5),
        3: (0.5, 1, 0, 0.5)
    }

    # Shading quadrants
    quadrant_colors = {
        0: 'lightblue',
        1: 'lightgreen',
        2: 'lightcoral',
        3: 'lightyellow'
    }
    for crystal, (x0, x1, y0, y1) in quadrant_boundaries.items():
        plt.fill_betweenx([y0, y1], x0, x1, color=quadrant_colors[crystal], alpha=0.2)

    # Plot individual events
    # for event in events:
    #     x, y = event.position  # Use position directly
        # plt.scatter(x, y, color='gray')
        # plt.text(x, y, f"{event.energy:.1f} keV", fontsize=9, verticalalignment='bottom')

    # Plot addback events
    for event in addback_events:
        color = next(colors)
        highest_crystal = event['highest_energy_crystal']
        for ce in event['coincident_events']:
            ce_x, ce_y = ce.position
            plt.scatter(ce_x, ce_y, color='k')
            # plt.text(ce_x, ce_y, f"{ce.energy:.1f} keV", fontsize=9, verticalalignment='top')

        # Draw segments connecting coincident events
        for k in range(len(event['coincident_events']) - 1):
            x0, y0 = event['coincident_events'][k].position
            x1, y1 = event['coincident_events'][k + 1].position
            if x0 != x1:
                plot_segments(x0, y0, x1, y0, color)  # Horizontal segment first
            if y0 != y1:
                plot_segments(x1, y0, x1, y1, color)  # Vertical segment next

    plt.xlabel('Position X')
    plt.ylabel('Position Y')
    plt.title('Addback Events')
    plt.grid(True)
    plt.show()

# Plot the events and addback process
plot_events(events, addback_events)

# Function to plot the energy spectrum from add-back events
def plot_energy_spectrum(addback_events):
    energies = [event['total_energy'] for event in addback_events]
    plt.figure(figsize=(10, 6))
    plt.hist(energies, bins=50, color='blue', alpha=0.7)
    plt.xlabel('Energy (keV)')
    plt.ylabel('Counts')
    plt.title('Adddback Events')
    plt.grid(True)
    plt.show()

# Plot the energy spectrum
plot_energy_spectrum(addback_events)
