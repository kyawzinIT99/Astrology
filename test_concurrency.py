import asyncio
import aiohttp
import time

URL = "https://kyawzin-ccna--astrology-chatbot-mm-wsgi-app.modal.run/api/bookings"

async def make_booking(session, index):
    payload = {
        "name": f"Test User {index}",
        "phone": f"09990000{index:02d}",
        "date": "2026-03-05", # Future date
        "time": "10:00 AM"
    }
    try:
        start = time.time()
        async with session.post(URL, json=payload) as response:
            if response.status != 201:
                text = await response.text()
                return f"[Req {index:02d}] Failed {response.status}: {text[:200]}"
            res_json = await response.json()
            elapsed = time.time() - start
            return f"[Req {index:02d}] Status: {response.status} | Time: {elapsed:.2f}s | Success: {res_json.get('success')}"
    except Exception as e:
        return f"[Req {index:02d}] Exception during request: {str(e)}"

async def main():
    print(f"Starting CONCURRENT stress test with 10 simultaneous bookings to: {URL}")
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        # Create 10 concurrent tasks
        tasks = [make_booking(session, i) for i in range(1, 11)]
        
        # Run them all at the exact same time
        results = await asyncio.gather(*tasks)
        
        for r in results:
            print(r)
            
    print(f"Total time for 10 concurrent requests: {time.time() - start_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
