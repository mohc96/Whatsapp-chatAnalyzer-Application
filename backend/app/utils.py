import re
import pandas as pd
from typing import Dict, List, Any, Optional
import datetime
import logging

logger = logging.getLogger(__name__)

class ChatFormatDetector:
    """Detect and handle different WhatsApp chat export formats"""
    
    @staticmethod
    def detect_format(text: str) -> str:
        """Detect the format of WhatsApp chat export"""
        lines = text.strip().split('\n')[:20]  # Check first 20 lines
        
        patterns = {
            'bracket_format': r'\[(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}:\d{2} [AP]M)\]',
            'dash_format': r'(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}) -',
            'space_format': r'(\d{1,2}/\d{1,2}/\d{2,4}) (\d{1,2}:\d{2}) -'
        }
        
        for format_name, pattern in patterns.items():
            matches = sum(1 for line in lines if re.search(pattern, line))
            if matches > 0:
                return format_name
        
        return 'unknown'

class DataValidator:
    """Validate chat data and provide helpful error messages"""
    
    @staticmethod
    def validate_chat_data(df: pd.DataFrame) -> Dict[str, Any]:
        """Validate the parsed chat data"""
        issues = []
        warnings = []
        
        # Check if DataFrame is empty
        if df.empty:
            issues.append("No valid messages found in the chat file")
        
        # Check for required columns
        required_columns = ['DateTime', 'person', 'message']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            issues.append(f"Missing required columns: {missing_columns}")
        
        # Check for null values
        if df.isnull().any().any():
            null_counts = df.isnull().sum()
            warnings.append(f"Found null values: {null_counts.to_dict()}")
        
        # Check date range
        if 'DateTime' in df.columns and not df['DateTime'].isnull().all():
            date_range = df['DateTime'].max() - df['DateTime'].min()
            if date_range.days < 1:
                warnings.append("Chat data spans less than a day")
        
        # Check for duplicate messages
        if 'message' in df.columns:
            duplicate_count = df['message'].duplicated().sum()
            if duplicate_count > 0:
                warnings.append(f"Found {duplicate_count} duplicate messages")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'total_messages': len(df) if not df.empty else 0
        }

class TextCleaner:
    """Clean and preprocess text data"""
    
    @staticmethod
    def clean_message(message: str) -> str:
        """Clean individual message text"""
        if not isinstance(message, str):
            return ""
        
        # Remove excessive whitespace
        message = re.sub(r'\s+', ' ', message.strip())
        
        # Remove system messages
        system_patterns = [
            r'<Media omitted>',
            r'image omitted',
            r'video omitted',
            r'audio omitted',
            r'document omitted',
            r'This message was deleted',
            r'You deleted this message',
            r'Messages to this chat and calls are now secured'
        ]
        
        for pattern in system_patterns:
            message = re.sub(pattern, '', message, flags=re.IGNORECASE)
        
        return message.strip()
    
    @staticmethod
    def extract_mentions(message: str) -> List[str]:
        """Extract @mentions from message"""
        return re.findall(r'@(\w+)', message)
    
    @staticmethod
    def extract_hashtags(message: str) -> List[str]:
        """Extract #hashtags from message"""
        return re.findall(r'#(\w+)', message)

class StatisticsCalculator:
    """Calculate various statistics from chat data"""
    
    @staticmethod
    def calculate_response_times(df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate response times between messages"""
        if df.empty or len(df) < 2:
            return {}
        
        df_sorted = df.sort_values('DateTime')
        response_times = []
        
        for i in range(1, len(df_sorted)):
            current_msg = df_sorted.iloc[i]
            prev_msg = df_sorted.iloc[i-1]
            
            # Only calculate if different persons
            if current_msg['person'] != prev_msg['person']:
                time_diff = current_msg['DateTime'] - prev_msg['DateTime']
                response_times.append(time_diff.total_seconds() / 60)  # in minutes
        
        if response_times:
            return {
                'avg_response_time_minutes': sum(response_times) / len(response_times),
                'median_response_time_minutes': sorted(response_times)[len(response_times)//2],
                'min_response_time_minutes': min(response_times),
                'max_response_time_minutes': max(response_times)
            }
        return {}
    
    @staticmethod
    def calculate_conversation_starters(df: pd.DataFrame) -> Dict[str, int]:
        """Calculate who starts conversations most often"""
        if df.empty:
            return {}
        
        df_sorted = df.sort_values('DateTime')
        starters = []
        
        # First message is always a starter
        starters.append(df_sorted.iloc[0]['person'])
        
        # Look for gaps > 1 hour to identify new conversations
        for i in range(1, len(df_sorted)):
            current_msg = df_sorted.iloc[i]
            prev_msg = df_sorted.iloc[i-1]
            
            time_diff = current_msg['DateTime'] - prev_msg['DateTime']
            if time_diff.total_seconds() > 3600:  # 1 hour gap
                starters.append(current_msg['person'])
        
        return dict(pd.Series(starters).value_counts())

def format_number(number: int) -> str:
    """Format large numbers with commas"""
    return f"{number:,}"

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.1f} minutes"
    elif seconds < 86400:
        return f"{seconds/3600:.1f} hours"
    else:
        return f"{seconds/86400:.1f} days"

def safe_divide(numerator: float, denominator: float) -> float:
    """Safely divide two numbers, return 0 if denominator is 0"""
    return numerator / denominator if denominator != 0 else 0.0

def get_time_period_label(hour: int) -> str:
    """Get time period label for an hour"""
    if 5 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 22:
        return "Evening"
    else:
        return "Night"