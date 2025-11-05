"""Quick script to verify database contents."""

import asyncio

from sqlalchemy import select

from app.core import setup_logging
from app.db import Frame, get_db_context


async def main():
    """Query and display frames from database."""
    setup_logging("INFO")
    
    print("\n" + "=" * 70)
    print("DATABASE VERIFICATION")
    print("=" * 70)
    
    async with get_db_context() as db:
        # Count total frames
        result = await db.execute(select(Frame))
        frames = result.scalars().all()
        
        print(f"\nTotal frames in database: {len(frames)}")
        
        if frames:
            print("\nFrame Details:")
            print("-" * 70)
            for frame in frames:
                print(f"Depth: {frame.depth:7.2f} | "
                      f"Dimensions: {frame.width}x{frame.height} | "
                      f"Size: {len(frame.image_png):,} bytes | "
                      f"Created: {frame.created_at}")
            
            # Show first frame details
            first_frame = frames[0]
            print("\n" + "=" * 70)
            print("FIRST FRAME DETAILS")
            print("=" * 70)
            print(f"Depth:        {first_frame.depth}")
            print(f"Width:        {first_frame.width}")
            print(f"Height:       {first_frame.height}")
            print(f"PNG Size:     {len(first_frame.image_png):,} bytes")
            print(f"PNG Header:   {first_frame.image_png[:8].hex()}")
            print(f"Created:      {first_frame.created_at}")
            print(f"Updated:      {first_frame.updated_at}")
            
            # Verify PNG signature
            png_sig = b'\x89PNG\r\n\x1a\n'
            is_valid_png = first_frame.image_png[:8] == png_sig
            print(f"Valid PNG:    {'✅ Yes' if is_valid_png else '❌ No'}")
        
        print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
