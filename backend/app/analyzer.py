import re
import pandas as pd
import numpy as np
from collections import Counter
from typing import Dict, List, Any
import datetime
import base64
import io
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import emoji_data_python as edp
import regex
import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
import string
from sklearn.feature_extraction.text import CountVectorizer
import warnings
warnings.filterwarnings('ignore')

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class WhatsAppChatAnalyzer:
    def __init__(self):
        self.stemmer = PorterStemmer()
        self.remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)
        plt.style.use('default')
        
    def parse_chat(self, raw_text: str) -> pd.DataFrame:
        """Parse WhatsApp chat text into structured DataFrame with support for multiple formats"""
        raw_text = raw_text.replace('\u202F', ' ')  # Normalize WhatsApp narrow space
        lines = raw_text.strip().split('\n')
        data = []
        
        # Define multiple regex patterns for different WhatsApp export formats
        patterns = [
            # Format 1: [M/D/YY, H:MM:SS AM/PM] Person: Message
            r'\[(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}:\d{2} [AP]M)\] ([^:]+): (.+)',
            
            # Format 2: [M/D/YY, H:MM:SS AM/PM] Person: Message (with optional leading ‎)
            r'‎?\[(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}:\d{2} [AP]M)\] ([^:]+): (.+)',
            
            # Format 3: DD/MM/YYYY, HH:MM - Person: Message
            r'(\d{1,2}/\d{1,2}/\d{4}), (\d{1,2}:\d{2}) - ([^:]+): (.+)',
            
            # Format 4: DD/MM/YY, HH:MM - Person: Message
            r'(\d{1,2}/\d{1,2}/\d{2}), (\d{1,2}:\d{2}) - ([^:]+): (.+)',
            
            # Format 5: M/D/YY, H:MM AM/PM - Person: Message
            r'(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2} [AP]M) - ([^:]+): (.+)',
            
            # Format 6: YYYY-MM-DD HH:MM:SS - Person: Message
            r'(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}) - ([^:]+): (.+)',
            
            # Format 7: DD.MM.YY, HH:MM - Person: Message
            r'(\d{1,2}\.\d{1,2}\.\d{2,4}), (\d{1,2}:\d{2}) - ([^:]+): (.+)',
        ]
        
        # Date format mappings for each pattern
        date_formats = [
            '%m/%d/%y %I:%M:%S %p',  # Format 1
            '%m/%d/%y %I:%M:%S %p',  # Format 2
            '%d/%m/%Y %H:%M',        # Format 3
            '%d/%m/%y %H:%M',        # Format 4
            '%m/%d/%y %I:%M %p',     # Format 5
            '%Y-%m-%d %H:%M:%S',     # Format 6
            '%d.%m.%y %H:%M',        # Format 7
        ]
        
        for line in lines:
            if line.strip():
                parsed = False
                
                # Try each pattern
                for i, pattern in enumerate(patterns):
                    match = re.match(pattern, line)
                    if match:
                        groups = match.groups()
                        date_str, time_str, sender, message = groups
                        
                        # Parse datetime based on the matched pattern
                        try:
                            if i in [0, 1, 4]:  # Formats with AM/PM
                                datetime_str = f"{date_str} {time_str}"
                            elif i == 5:  # Format 6 - separate date and time
                                datetime_str = f"{date_str} {time_str}"
                            else:  # Other formats
                                datetime_str = f"{date_str} {time_str}"
                                
                            dt = pd.to_datetime(datetime_str, format=date_formats[i])
                            
                            data.append({
                                "DateTime": dt,
                                "person": sender.strip(),
                                "message": message.strip()
                            })
                            parsed = True
                            break
                            
                        except Exception as e:
                            # Try with different year formats if parsing fails
                            try:
                                if i in [0, 1]:  # Try 4-digit year
                                    alt_format = '%m/%d/%Y %I:%M:%S %p'
                                elif i == 3:  # Try 4-digit year for format 4
                                    alt_format = '%d/%m/%Y %H:%M'
                                elif i == 6:  # Try 4-digit year for format 7
                                    alt_format = '%d.%m.%Y %H:%M'
                                else:
                                    continue
                                    
                                dt = pd.to_datetime(datetime_str, format=alt_format)
                                data.append({
                                    "DateTime": dt,
                                    "person": sender.strip(),
                                    "message": message.strip()
                                })
                                parsed = True
                                break
                            except:
                                continue
                
                if not parsed:
                    # Handle multiline messages (continuation of previous message)
                    if data and line.strip() and not any(re.match(p, line) for p in patterns):
                        # This might be a continuation of the previous message
                        if not line.startswith('[') and not line.startswith('‎['):
                            data[-1]["message"] += "\n" + line.strip()
        
        if not data:
            raise ValueError("No valid chat messages found. Please check the chat format.")
        
        df = pd.DataFrame(data)
        
        # Filter out system messages and deleted messages
        system_messages = [
            "omitted", "deleted", "missed voice call", "missed video call", 
            "end-to-end encrypted", "you deleted this message", "this message was deleted",
            "messages and calls are end-to-end encrypted", "image omitted", "video omitted",
            "audio omitted", "document omitted", "contact omitted", "location omitted",
            "sticker omitted", "gif omitted"
        ]
        
        # Create a mask for filtering
        mask = pd.Series([True] * len(df))
        for msg in system_messages:
            mask &= ~df["message"].str.contains(msg, case=False, na=False, regex=False)
        
        df = df[mask].copy()
        
        # Reset index after filtering
        df.reset_index(drop=True, inplace=True)
        
        if len(df) == 0:
            raise ValueError("No valid messages found after filtering system messages.")
        
        # Add time-based columns
        df['weekday'] = df['DateTime'].dt.day_name()
        df['month'] = df['DateTime'].dt.month_name()
        df['year'] = df['DateTime'].dt.year
        df['date'] = df['DateTime'].dt.date
        df['time'] = df['DateTime'].dt.time
        
        # Add message statistics
        df['letter_count'] = df['message'].str.len()
        df['word_count'] = df['message'].str.split().str.len()
        
        # URL count
        url_pattern = r'(https?://\S+)'
        df['urlcount'] = df['message'].apply(lambda x: len(re.findall(url_pattern, x)))
        
        # Emoji extraction
        df['emoji'] = df['message'].apply(self._extract_emojis)
        
        return df
    
    def _extract_emojis(self, text: str) -> List[str]:
        """Extract emojis from text"""
        try:
            emoji_list = []
            data = regex.findall(r'\X', text)
            for word in data:
                if any(char in edp.emoji_data for char in word):
                    emoji_list.append(word)
            return emoji_list
        except:
            return []
    
    def _get_tokens(self, text: str) -> List[str]:
        """Tokenize and process text for analysis"""
        try:
            # Convert to lowercase
            lowers = text.lower()
            # Remove punctuation
            no_punctuation = lowers.translate(self.remove_punctuation_map)
            # Tokenize
            tokens = nltk.word_tokenize(no_punctuation)
            # Remove stop words
            filtered = [w for w in tokens if w not in stopwords.words('english')]
            # Stemming
            stemmed = [self.stemmer.stem(item) for item in filtered]
            return stemmed
        except:
            return []
    
    def generate_visualizations(self, df: pd.DataFrame) -> Dict[str, str]:
        """Generate base64 encoded visualizations"""
        visualizations = {}
        
        # Set style
        plt.style.use('seaborn-v0_8')
        
        # 1. Messages by weekday
        plt.figure(figsize=(12, 6))
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df['weekday'] = pd.Categorical(df['weekday'], categories=weekday_order, ordered=True)
        sns.countplot(data=df, x='weekday', hue='person')
        plt.title('Messages by Day of Week')
        plt.xticks(rotation=45)
        plt.tight_layout()
        visualizations['weekday_chart'] = self._fig_to_base64()
        
        # 2. Messages by month
        plt.figure(figsize=(12, 6))
        sns.countplot(data=df, x='month', hue='person')
        plt.title('Messages by Month')
        plt.xticks(rotation=45)
        plt.tight_layout()
        visualizations['month_chart'] = self._fig_to_base64()
        
        # 3. Messages over time
        plt.figure(figsize=(15, 6))
        daily_messages = df.groupby('date').size()
        plt.plot(daily_messages.index, daily_messages.values, color='#1f77b4', linewidth=2)
        plt.title('Messages Over Time')
        plt.xlabel('Date')
        plt.ylabel('Number of Messages')
        plt.xticks(rotation=45)
        plt.tight_layout()
        visualizations['timeline_chart'] = self._fig_to_base64()
        
        # 4. Message distribution pie chart
        plt.figure(figsize=(10, 8))
        person_counts = df['person'].value_counts()
        plt.pie(person_counts.values, labels=person_counts.index, autopct='%1.1f%%', startangle=90)
        plt.title('Message Distribution by Person')
        plt.tight_layout()
        visualizations['pie_chart'] = self._fig_to_base64()
        
        # 5. Word cloud
        if len(df) > 0:
            all_text = ' '.join(df['message'].astype(str))
            if all_text.strip():  # Only create wordcloud if there's text
                wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_text)
                plt.figure(figsize=(12, 6))
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis('off')
                plt.title('Word Cloud')
                plt.tight_layout()
                visualizations['wordcloud'] = self._fig_to_base64()
        
        return visualizations
    
    def _fig_to_base64(self) -> str:
        """Convert matplotlib figure to base64 string"""
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        return image_base64
    
    def analyze_chat(self, raw_text: str) -> Dict[str, Any]:
        """Main analysis function"""
        try:
            df = self.parse_chat(raw_text)
            
            # Basic statistics
            total_messages = len(df)
            unique_users = df['person'].nunique()
            date_range = {
                'start': df['DateTime'].min().isoformat(),
                'end': df['DateTime'].max().isoformat()
            }
            
            # Top senders
            top_senders = df['person'].value_counts().head(10).to_dict()
            
            # Message statistics
            avg_message_length = df['letter_count'].mean()
            avg_words_per_message = df['word_count'].mean()
            
            # Most active times
            df['hour'] = df['DateTime'].dt.hour
            hourly_activity = df['hour'].value_counts().sort_index().to_dict()
            
            # Most active days
            daily_activity = df['weekday'].value_counts().to_dict()
            
            # Monthly activity
            monthly_activity = df['month'].value_counts().to_dict()
            
            # Top words (excluding stop words)
            all_messages = ' '.join(df['message'].astype(str))
            tokens = self._get_tokens(all_messages)
            word_freq = Counter(tokens)
            top_words = dict(word_freq.most_common(20))
            
            # Emoji analysis
            all_emojis = []
            for emoji_list in df['emoji']:
                all_emojis.extend(emoji_list)
            emoji_freq = Counter(all_emojis)
            top_emojis = dict(emoji_freq.most_common(10))
            
            # URL and media statistics
            total_urls = df['urlcount'].sum()
            
            # Generate visualizations
            visualizations = self.generate_visualizations(df)
            
            return {
                "summary": {
                    "total_messages": int(total_messages),
                    "unique_users": int(unique_users),
                    "date_range": date_range,
                    "avg_message_length": round(avg_message_length, 2),
                    "avg_words_per_message": round(avg_words_per_message, 2),
                    "total_urls_shared": int(total_urls)
                },
                "user_activity": {
                    "top_senders": top_senders,
                    "hourly_activity": hourly_activity,
                    "daily_activity": daily_activity,
                    "monthly_activity": monthly_activity
                },
                "content_analysis": {
                    "top_words": top_words,
                    "top_emojis": top_emojis
                },
                "visualizations": visualizations
            }
            
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")


# Global analyzer instance
analyzer = WhatsAppChatAnalyzer()

def analyze_chat(raw_text: str) -> Dict[str, Any]:
    """Main function to analyze WhatsApp chat"""
    return analyzer.analyze_chat(raw_text)