import pandas as pd
from datetime import datetime, timedelta
import json

def parse_schedule(file_path, group_name):
    # Read the Excel file
    df = pd.read_excel(file_path, header=None)
    
    # Define session times
    session_times = [
        "09:00-10:30", "10:45-12:15", "13:00-14:30",
        "14:40-16:10", "16:20-17:50", "18:00-19:30"
    ]
    
    # Define base date (start from April 14, 2025)
    base_date = datetime(2025, 4, 14)
    
    # Initialize the schedule structure
    schedule = []
    
    # Find the column index for the specified group
    header_row = df.iloc[0]
    group_col = None
    for col in range(len(header_row)):
        if isinstance(header_row[col], str) and group_name in header_row[col]:
            group_col = col
            break
    
    if group_col is None:
        return {"schedule": [], "error": f"Group {group_name} not found"}
    
    # Process the dataframe to identify blocks of days
    current_date = base_date
    session_block = []
    session_index = 0
    
    for index, row in df.iterrows():
        # Check if row contains session time (e.g., "1 пара")
        if isinstance(row[0], str) and "пара" in row[0]:
            if session_index < len(session_times):
                sessions = []
                # Extract subject and cabinet for the group
                subject = row[group_col] if pd.notna(row[group_col]) else ""
                cabinet = row[group_col+1] if group_col+1 < len(row) and pd.notna(row[group_col+1]) else ""
                
                # Extract teacher from subject string (usually follows a comma)
                teacher = ""
                if subject and "," in subject:
                    parts = subject.split(",", 1)
                    subject = parts[0].strip()
                    teacher = parts[1].strip() if len(parts) > 1 else ""
                
                if subject or cabinet:  # Only add if there's meaningful data
                    sessions.append({
                        "time": session_times[session_index],
                        "subject": subject,
                        "teacher": teacher,
                        "cabinet": cabinet
                    })
                
                session_block.append(sessions)
                session_index += 1
        else:
            # End of a day block, reset for next day
            if session_block:
                # Aggregate sessions for the current day
                day_schedule = {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "sessions": []
                }
                # Add sessions for the group
                for session_list in session_block:
                    for session in session_list:
                        day_schedule["sessions"].append(session)
                
                if day_schedule["sessions"]:  # Only add if there are sessions
                    schedule.append(day_schedule)
                session_block = []
                session_index = 0
                current_date += timedelta(days=1)
    
    # Handle the last day if any sessions remain
    if session_block:
        day_schedule = {
            "date": current_date.strftime("%Y-%m-%d"),
            "sessions": []
        }
        for session_list in session_block:
            for session in session_list:
                day_schedule["sessions"].append(session)
        if day_schedule["sessions"]:  # Only add if there are sessions
            schedule.append(day_schedule)
    
    # Return the JSON structure
    return {
        "schedule": schedule
    }

# Example usage
if __name__ == "__main__":
    file_path = "14.04 - 18.04-1.xlsx"
    group_name = "ИСИП-306"
    result = parse_schedule(file_path, group_name)
    print(json.dumps(result, indent=2, ensure_ascii=False))
