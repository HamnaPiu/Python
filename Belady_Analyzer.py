import Algo_fifo

def run_belady_test(trace_data):
    """
    Tests FIFO with frame counts from 2 to 10 to find anomalies[cite: 1].
    """
    print(f"{'Frames':<10} | {'Page Faults':<12} | {'Anomaly Detected'}")
    print("-" * 45)
    
    results = []
    
    # Testing different physical memory capacities[cite: 1]
    for frame_count in range(2, 11):
        # Assuming your FIFO class takes frame_count as an argument
        fifo = Algo_fifo.FIFO(capacity=frame_count)
        faults = 0
        
        for vpn in trace_data:
            if not fifo.access(vpn): # returns False if fault
                faults += 1
                fifo.replace(vpn)
        
        anomaly = "YES!" if results and faults > results[-1] else ""
        print(f"{frame_count:<10} | {faults:<12} | {anomaly}")
        results.append(faults)

# Example usage with a known sequence that causes Belady's Anomaly[cite: 1]
# reference_string = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]