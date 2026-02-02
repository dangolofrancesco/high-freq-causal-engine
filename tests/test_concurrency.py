import engine_core
import threading
import time
import random

print("--- CONCURRENCY TEST ---")

book = engine_core.OrderBook()
running = True

def writer_job():
    """Simulates the market rapidly sending orders"""
    count = 0
    while running:
        # Random price and quantity
        p = 100.0 + random.uniform(-5, 5)
        q = random.uniform(0.1, 2.0)
        is_bid = random.choice([True, False])
        
        book.add_order(p, q, is_bid)
        count += 1
        # Simulate a tiny delay to mimic real-world conditions
        time.sleep(0.0001) 
    print(f"Writer Thread has inserted {count} orders.")

def reader_job():
    """Simulates the strategy reading the imbalance"""
    read_count = 0
    while running:
        try:
            # Without the mutex, this call while the other writes
            # would crash everything.
            obi = book.get_imbalance()
            read_count += 1
        except Exception as e:
            print(f"READ ERROR: {e}")
            break
    print(f"Reader Thread has read {read_count} times.")

# Start the threads
t_writer = threading.Thread(target=writer_job)
t_reader = threading.Thread(target=reader_job)

print("Starting simultaneous threads for 2 seconds...")
t_writer.start()
t_reader.start()

time.sleep(2) # Let the chaos run for 2 seconds

running = False # Stop
t_writer.join()
t_reader.join()

print("\n✅ TEST COMPLETED")
print(f"Final Orders in Book: {book.get_bid_count() + book.get_ask_count()}")
print("If you see this message without strange errors or crashes, the C++ Mutex works!")