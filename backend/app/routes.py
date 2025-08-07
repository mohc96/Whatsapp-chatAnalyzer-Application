# from fastapi import APIRouter, UploadFile, File, HTTPException
# from fastapi.responses import JSONResponse
# from app.analyzer import analyze_chat
# import logging

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# router = APIRouter()

# @router.post("/analyze")
# async def analyze_whatsapp_chat(file: UploadFile = File(...)):
#     """
#     Analyze WhatsApp chat file and return comprehensive insights
    
#     Args:
#         file: WhatsApp chat export file (.txt format)
    
#     Returns:
#         JSON response with analysis results including:
#         - Summary statistics
#         - User activity patterns
#         - Content analysis
#         - Visualizations (base64 encoded)
#     """
#     try:
#         # Validate file type
#         if not file.filename.endswith('.txt'):
#             raise HTTPException(
#                 status_code=400, 
#                 detail="Please upload a WhatsApp chat export file (.txt format)"
#             )
        
#         # Read file contents
#         contents = await file.read()
        
#         # Decode with error handling
#         try:
#             text_content = contents.decode("utf-8")
#         except UnicodeDecodeError:
#             try:
#                 text_content = contents.decode("latin-1")
#             except UnicodeDecodeError:
#                 raise HTTPException(
#                     status_code=400,
#                     detail="Unable to decode file. Please ensure it's a valid text file."
#                 )
        
#         # Validate content
#         if not text_content.strip():
#             raise HTTPException(
#                 status_code=400,
#                 detail="File appears to be empty"
#             )
        
#         logger.info(f"Analyzing chat file: {file.filename}")
        
#         # Perform analysis
#         result = analyze_chat(text_content)
        
#         logger.info("Analysis completed successfully")
        
#         return JSONResponse(content={
#             "status": "success",
#             "filename": file.filename,
#             "data": result
#         })
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Analysis failed: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Analysis failed: {str(e)}"
#         )

# @router.get("/health")
# async def health_check():
#     """Health check endpoint"""
#     return {"status": "healthy", "message": "WhatsApp Chat Analyzer API is running"}

# @router.get("/")
# async def root():
#     """Root endpoint with API information"""
#     return {
#         "message": "WhatsApp Chat Analyzer API",
#         "version": "1.0.0",
#         "endpoints": {
#             "analyze": "/analyze - POST - Upload WhatsApp chat file for analysis",
#             "health": "/health - GET - Health check",
#             "docs": "/docs - Interactive API documentation"
#         }
#     }

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from app.analyzer import WhatsAppChatAnalyzer
import logging
import pandas as pd
from typing import Optional, Dict, Any, List
import json
import tempfile
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Global storage for processed data (in production, use Redis or database)
# For demo purposes, we'll use in-memory storage
chat_sessions = {}

analyzer = WhatsAppChatAnalyzer()

@router.post("/upload")
async def upload_chat_file(file: UploadFile = File(...)):
    """
    Upload and parse WhatsApp chat file
    Returns a session ID for subsequent API calls
    """
    try:
        # Validate file type
        if not file.filename.endswith('.txt'):
            raise HTTPException(
                status_code=400, 
                detail="Please upload a WhatsApp chat export file (.txt format)"
            )
        
        # Read file contents
        contents = await file.read()
        
        # Decode with error handling
        try:
            text_content = contents.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text_content = contents.decode("latin-1")
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Unable to decode file. Please ensure it's a valid text file."
                )
        
        # Validate content
        if not text_content.strip():
            raise HTTPException(
                status_code=400,
                detail="File appears to be empty"
            )
        
        logger.info(f"Processing chat file: {file.filename}")
        
        # Parse chat data
        df = analyzer.parse_chat(text_content)
        
        # Generate session ID
        session_id = f"session_{len(chat_sessions) + 1}"
        
        # Store parsed data
        chat_sessions[session_id] = {
            "filename": file.filename,
            "dataframe": df,
            "raw_text": text_content
        }
        
        logger.info(f"Chat processed successfully. Session ID: {session_id}")
        
        return JSONResponse(content={
            "status": "success",
            "session_id": session_id,
            "filename": file.filename,
            "message": "Chat file uploaded and processed successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

@router.get("/summary/{session_id}")
async def get_chat_summary(session_id: str):
    """Get basic chat statistics and summary"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        df = chat_sessions[session_id]["dataframe"]
        
        # Basic statistics
        total_messages = len(df)
        unique_users = df['person'].nunique()
        date_range = {
            'start': df['DateTime'].min().isoformat(),
            'end': df['DateTime'].max().isoformat()
        }
        
        # Message statistics
        avg_message_length = df['letter_count'].mean()
        avg_words_per_message = df['word_count'].mean()
        total_urls = df['urlcount'].sum()
        
        # Top senders
        top_senders = df['person'].value_counts().head(10).to_dict()
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "total_messages": int(total_messages),
                "unique_users": int(unique_users),
                "date_range": date_range,
                "avg_message_length": round(avg_message_length, 2),
                "avg_words_per_message": round(avg_words_per_message, 2),
                "total_urls_shared": int(total_urls),
                "top_senders": top_senders
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summary generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

@router.get("/activity/{session_id}")
async def get_activity_patterns(session_id: str):
    """Get user activity patterns (hourly, daily, monthly)"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        df = chat_sessions[session_id]["dataframe"]
        
        # Add hour column if not exists
        if 'hour' not in df.columns:
            df['hour'] = df['DateTime'].dt.hour
        
        # Activity patterns
        hourly_activity = df['hour'].value_counts().sort_index().to_dict()
        daily_activity = df['weekday'].value_counts().to_dict()
        monthly_activity = df['month'].value_counts().to_dict()
        
        # Activity by person
        activity_by_person = {}
        for person in df['person'].unique():
            person_df = df[df['person'] == person]
            activity_by_person[person] = {
                "hourly": person_df['hour'].value_counts().sort_index().to_dict(),
                "daily": person_df['weekday'].value_counts().to_dict(),
                "monthly": person_df['month'].value_counts().to_dict()
            }
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "overall": {
                    "hourly_activity": hourly_activity,
                    "daily_activity": daily_activity,
                    "monthly_activity": monthly_activity
                },
                "by_person": activity_by_person
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Activity analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Activity analysis failed: {str(e)}")

@router.get("/content/{session_id}")
async def get_content_analysis(session_id: str, top_words: int = Query(20, ge=1, le=100)):
    """Get content analysis (words, emojis, etc.)"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        df = chat_sessions[session_id]["dataframe"]
        
        # Word analysis
        all_messages = ' '.join(df['message'].astype(str))
        tokens = analyzer._get_tokens(all_messages)
        word_freq = Counter(tokens)
        top_words_dict = dict(word_freq.most_common(top_words))
        
        # Emoji analysis
        all_emojis = []
        for emoji_list in df['emoji']:
            all_emojis.extend(emoji_list)
        emoji_freq = Counter(all_emojis)
        top_emojis = dict(emoji_freq.most_common(10))
        
        # Content by person
        content_by_person = {}
        for person in df['person'].unique():
            person_df = df[df['person'] == person]
            person_messages = ' '.join(person_df['message'].astype(str))
            person_tokens = analyzer._get_tokens(person_messages)
            person_word_freq = Counter(person_tokens)
            
            person_emojis = []
            for emoji_list in person_df['emoji']:
                person_emojis.extend(emoji_list)
            person_emoji_freq = Counter(person_emojis)
            
            content_by_person[person] = {
                "top_words": dict(person_word_freq.most_common(10)),
                "top_emojis": dict(person_emoji_freq.most_common(5)),
                "total_words": len(person_tokens),
                "total_emojis": len(person_emojis)
            }
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "overall": {
                    "top_words": top_words_dict,
                    "top_emojis": top_emojis,
                    "total_unique_words": len(word_freq),
                    "total_emojis": len(all_emojis)
                },
                "by_person": content_by_person
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Content analysis failed: {str(e)}")

@router.get("/timeline/{session_id}")
async def get_timeline_data(session_id: str, granularity: str = Query("daily", regex="^(daily|weekly|monthly)$")):
    """Get timeline data for chat activity"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        df = chat_sessions[session_id]["dataframe"]
        
        if granularity == "daily":
            timeline = df.groupby('date').size().reset_index(name='count')
            timeline['date'] = timeline['date'].astype(str)
        elif granularity == "weekly":
            df['week'] = df['DateTime'].dt.to_period('W')
            timeline = df.groupby('week').size().reset_index(name='count')
            timeline['date'] = timeline['week'].astype(str)
            timeline = timeline.drop('week', axis=1)
        else:  # monthly
            df['month_year'] = df['DateTime'].dt.to_period('M')
            timeline = df.groupby('month_year').size().reset_index(name='count')
            timeline['date'] = timeline['month_year'].astype(str)
            timeline = timeline.drop('month_year', axis=1)
        
        # Timeline by person
        timeline_by_person = {}
        for person in df['person'].unique():
            person_df = df[df['person'] == person]
            if granularity == "daily":
                person_timeline = person_df.groupby('date').size().reset_index(name='count')
                person_timeline['date'] = person_timeline['date'].astype(str)
            elif granularity == "weekly":
                person_df['week'] = person_df['DateTime'].dt.to_period('W')
                person_timeline = person_df.groupby('week').size().reset_index(name='count')
                person_timeline['date'] = person_timeline['week'].astype(str)
                person_timeline = person_timeline.drop('week', axis=1)
            else:  # monthly
                person_df['month_year'] = person_df['DateTime'].dt.to_period('M')
                person_timeline = person_df.groupby('month_year').size().reset_index(name='count')
                person_timeline['date'] = person_timeline['month_year'].astype(str)
                person_timeline = person_timeline.drop('month_year', axis=1)
            
            timeline_by_person[person] = person_timeline.to_dict('records')
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "overall": timeline.to_dict('records'),
                "by_person": timeline_by_person,
                "granularity": granularity
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Timeline analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Timeline analysis failed: {str(e)}")

@router.get("/visualizations/{session_id}")
async def get_visualizations(session_id: str, chart_type: Optional[str] = Query(None)):
    """Get visualization data (base64 encoded charts)"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        df = chat_sessions[session_id]["dataframe"]
        
        if chart_type:
            # Return specific chart
            if chart_type == "weekday":
                visualizations = {"weekday_chart": analyzer.generate_visualizations(df)["weekday_chart"]}
            elif chart_type == "month":
                visualizations = {"month_chart": analyzer.generate_visualizations(df)["month_chart"]}
            elif chart_type == "timeline":
                visualizations = {"timeline_chart": analyzer.generate_visualizations(df)["timeline_chart"]}
            elif chart_type == "pie":
                visualizations = {"pie_chart": analyzer.generate_visualizations(df)["pie_chart"]}
            elif chart_type == "wordcloud":
                visualizations = {"wordcloud": analyzer.generate_visualizations(df)["wordcloud"]}
            else:
                raise HTTPException(status_code=400, detail="Invalid chart type")
        else:
            # Return all visualizations
            visualizations = analyzer.generate_visualizations(df)
        
        return JSONResponse(content={
            "status": "success",
            "data": visualizations
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Visualization generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Visualization generation failed: {str(e)}")

@router.get("/search/{session_id}")
async def search_messages(
    session_id: str, 
    query: str = Query(..., min_length=1),
    person: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000)
):
    """Search messages by content and/or person"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        df = chat_sessions[session_id]["dataframe"]
        
        # Filter by person if specified
        if person:
            df = df[df['person'] == person]
        
        # Search messages
        search_results = df[df['message'].str.contains(query, case=False, na=False)]
        
        # Limit results
        search_results = search_results.head(limit)
        
        # Convert to dict for JSON response
        results = []
        for _, row in search_results.iterrows():
            results.append({
                "datetime": row['DateTime'].isoformat(),
                "person": row['person'],
                "message": row['message'],
                "word_count": row['word_count'],
                "letter_count": row['letter_count']
            })
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "query": query,
                "person_filter": person,
                "total_results": len(search_results),
                "results": results
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    sessions = []
    for session_id, data in chat_sessions.items():
        df = data["dataframe"]
        sessions.append({
            "session_id": session_id,
            "filename": data["filename"],
            "total_messages": len(df),
            "date_range": {
                "start": df['DateTime'].min().isoformat(),
                "end": df['DateTime'].max().isoformat()
            }
        })
    
    return JSONResponse(content={
        "status": "success",
        "data": sessions
    })

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del chat_sessions[session_id]
    
    return JSONResponse(content={
        "status": "success",
        "message": f"Session {session_id} deleted successfully"
    })

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "WhatsApp Chat Analyzer API is running"}

@router.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "WhatsApp Chat Analyzer API - Modular Version",
        "version": "2.0.0",
        "endpoints": {
            "upload": "/upload - POST - Upload WhatsApp chat file",
            "summary": "/summary/{session_id} - GET - Basic chat statistics",
            "activity": "/activity/{session_id} - GET - Activity patterns",
            "content": "/content/{session_id} - GET - Content analysis",
            "timeline": "/timeline/{session_id} - GET - Timeline data",
            "visualizations": "/visualizations/{session_id} - GET - Chart visualizations",
            "search": "/search/{session_id} - GET - Search messages",
            "sessions": "/sessions - GET - List active sessions",
            "delete": "/sessions/{session_id} - DELETE - Delete session",
            "health": "/health - GET - Health check",
            "docs": "/docs - Interactive API documentation"
        }
    }