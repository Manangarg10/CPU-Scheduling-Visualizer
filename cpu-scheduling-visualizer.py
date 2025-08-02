import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import time as systime
from collections import deque
import random
import time

st.set_page_config(layout="wide")

# App State
if "process_list" not in st.session_state:
    st.session_state.process_list = []
if "timeline" not in st.session_state:
    st.session_state.timeline = []
if "completed" not in st.session_state:
    st.session_state.completed = []
if "execution_time" not in st.session_state:
    st.session_state.execution_time = None
if "comparison_times" not in st.session_state:
    st.session_state.comparison_times = {}

# Add Task Form
with st.sidebar.form("add_task"):
    st.markdown("### ➕ Add a New Task")
    pid = st.text_input("Process ID", value=f"P{len(st.session_state.process_list)+1}")
    at = st.number_input("Arrival Time", value=0, min_value=0)
    bt = st.number_input("Burst Time", value=5, min_value=1)
    pr = st.number_input("Priority", value=1, min_value=1)
    submitted = st.form_submit_button("Add Process")
    if submitted:
        st.session_state.process_list.append((pid, at, bt, pr))

# Display Current Tasks
tab1, tab2, tab3 = st.tabs(["🔧 Setup & Simulation", "📊 Timeline & Results", "📈 Comparison Graph"])

with tab1:
    st.markdown("### 🧾 Current Processes")
    df = pd.DataFrame(st.session_state.process_list, columns=["PID", "Arrival", "Burst", "Priority"])
    st.dataframe(df, use_container_width=True)

    algo = st.selectbox("Select Algorithm", ["FCFS", "SJF", "Round Robin", "Priority"])
    quantum = st.number_input("Time Quantum (only for Round Robin)", min_value=1, value=2) if algo == "Round Robin" else None

    def run_simulation(processes, algo, quantum):
        time = 0
        timeline = []
        ready_queue = deque()
        completed = []
        waiting = sorted(processes, key=lambda x: x[1])
        remaining_bt = {p[0]: p[2] for p in processes}

        i = 0
        while len(completed) < len(processes):
            while i < len(waiting) and waiting[i][1] <= time:
                ready_queue.append(waiting[i])
                i += 1

            if algo == "SJF":
                ready_queue = deque(sorted(ready_queue, key=lambda x: x[2]))
            elif algo == "Priority":
                ready_queue = deque(sorted(ready_queue, key=lambda x: x[3]))

            if not ready_queue:
                timeline.append(("Idle", time, time + 1))
                time += 1
                continue

            current = ready_queue.popleft()
            pid, at, bt, pr = current
            start = time

            if algo == "Round Robin":
                exec_time = min(quantum, remaining_bt[pid])
                remaining_bt[pid] -= exec_time
                time += exec_time
                timeline.append((pid, start, time))
                if remaining_bt[pid] > 0:
                    ready_queue.append((pid, time, bt, pr))
                else:
                    completed.append(pid)
            else:
                time += bt
                timeline.append((pid, start, time))
                completed.append(pid)

        return timeline, completed

    if st.button("🚀 Start Simulation"):
        if not st.session_state.process_list:
            st.warning("Please add at least one process before starting the simulation.")
        else:
            start_time = time.time()
            st.session_state.timeline, st.session_state.completed = run_simulation(st.session_state.process_list, algo, quantum)
            end_time = time.time()
            exec_time = round((end_time - start_time) * 1000, 2)  # in milliseconds
            st.session_state.execution_time = exec_time
            st.session_state.comparison_times[algo] = exec_time

with tab2:
    st.markdown("### 📈 CPU Gantt Chart (Animated Smooth Blocks)")
    if st.session_state.timeline:
        st.warning("Note: Smooth animation best visible for short simulations.")
        fig, ax = plt.subplots(figsize=(12, 2))
        ax.set_ylim(0, 2)
        ax.set_xlim(0, max(end for _, _, end in st.session_state.timeline) + 1)
        ax.set_xlabel("Time")
        ax.set_yticks([])
        ax.set_title("CPU Execution Timeline (Smooth Gantt Chart)")

        color_map = {}
        color_cycle = list(plt.cm.get_cmap("tab20").colors)
        plot_placeholder = st.empty()

        max_time = int(max(end for _, _, end in st.session_state.timeline))
        for current_time in range(0, max_time + 1):
            ax.clear()
            ax.set_ylim(0, 2)
            ax.set_xlim(0, max_time + 1)
            ax.set_xlabel("Time")
            ax.set_yticks([])
            ax.set_title("CPU Execution Timeline (Gantt Chart)")

            for pid, start, end in st.session_state.timeline:
                if pid not in color_map:
                    color_map[pid] = color_cycle[len(color_map) % len(color_cycle)]
                if current_time >= start:
                    draw_end = min(current_time, end)
                    ax.broken_barh([(start, draw_end - start)], (0.5, 0.9), facecolors=color_map[pid])
                    ax.text((start + draw_end) / 2, 0.95, f"{pid}", ha='center', va='center', color='white', fontsize=8)

            plot_placeholder.pyplot(fig)
            systime.sleep(0.3)

        st.success(f"Simulation completed in {st.session_state.execution_time} ms")
    else:
        st.info("Run a simulation to see the Gantt chart.")



with tab3:
    st.markdown("### 📉 Algorithm Execution Time Comparison")
    if st.session_state.comparison_times:
        df_compare = pd.DataFrame(list(st.session_state.comparison_times.items()), columns=["Algorithm", "Execution Time (ms)"])
        fig, ax = plt.subplots()
        ax.bar(df_compare["Algorithm"], df_compare["Execution Time (ms)"], color='skyblue')
        ax.set_title("Execution Time per Scheduling Algorithm")
        ax.set_ylabel("Time (ms)")
        st.pyplot(fig)
    else:
        st.info("Run simulations for different algorithms to compare their performance here.")

st.sidebar.markdown("---")
st.sidebar.markdown("Made for OS Simulation — PyCharm & Streamlit")
