#!/usr/bin/env python3
"""
SQLite Database Manager for AI Travel Assistant

This module handles all database operations including:
- Agent configuration
- Personality templates  
- User preferences
- Booking information (car, hotel)
- Conversation history
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager


class DatabaseManager:
    """Manages SQLite database operations for the travel assistant"""
    
    def __init__(self, db_path: str = "data/travel_assistant.db"):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_tables()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def _create_tables(self):
        """Create all required database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Agent Configuration Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL DEFAULT 'AI Travel Assistant',
                    personality TEXT NOT NULL DEFAULT 'friendly',
                    avatar TEXT NOT NULL DEFAULT '🤖',
                    tone TEXT NOT NULL DEFAULT 'casual',
                    emoji_usage TEXT NOT NULL DEFAULT 'moderate',
                    creativity REAL NOT NULL DEFAULT 0.7,
                    context_messages INTEGER NOT NULL DEFAULT 5,
                    show_tool_info BOOLEAN NOT NULL DEFAULT 1,
                    show_context_preview BOOLEAN NOT NULL DEFAULT 1,
                    enable_tts BOOLEAN NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Personality Templates Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personality_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    personality_type TEXT NOT NULL UNIQUE,
                    description TEXT NOT NULL,
                    greeting_messages TEXT NOT NULL, -- JSON array
                    response_style TEXT NOT NULL,   -- JSON object
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User Preferences Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL DEFAULT 'default',
                    travel_interests TEXT, -- JSON array
                    budget_preference TEXT DEFAULT 'medium',
                    dietary_restrictions TEXT, -- JSON array
                    favorite_cuisines TEXT, -- JSON array
                    bucket_list TEXT, -- JSON array
                    visited_places TEXT, -- JSON array
                    remember_preferences BOOLEAN DEFAULT 1,
                    proactive_suggestions BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Car Booking Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS book_car (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL DEFAULT 'default',
                    pickup_location TEXT NOT NULL,
                    dropoff_location TEXT,
                    pickup_date DATE NOT NULL,
                    pickup_time TIME,
                    return_date DATE,
                    return_time TIME,
                    car_type TEXT, -- economy, standard, luxury
                    driver_needed BOOLEAN DEFAULT 0,
                    passengers INTEGER DEFAULT 1,
                    special_requirements TEXT,
                    estimated_cost REAL,
                    booking_status TEXT DEFAULT 'pending', -- pending, confirmed, cancelled
                    booking_reference TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Hotel Booking Table  
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS book_hotel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL DEFAULT 'default',
                    hotel_name TEXT,
                    location TEXT NOT NULL,
                    checkin_date DATE NOT NULL,
                    checkout_date DATE NOT NULL,
                    adults INTEGER NOT NULL DEFAULT 1,
                    children INTEGER DEFAULT 0,
                    room_type TEXT, -- single, double, suite
                    room_count INTEGER DEFAULT 1,
                    budget_range TEXT, -- budget, mid-range, luxury
                    amenities TEXT, -- JSON array
                    special_requests TEXT,
                    estimated_cost REAL,
                    booking_status TEXT DEFAULT 'pending',
                    booking_reference TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Conversations Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL DEFAULT 'default',
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 0
                )
            """)
            
            # Conversation History Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    message_type TEXT NOT NULL, -- user, assistant, system
                    message_content TEXT NOT NULL,
                    metadata TEXT, -- JSON for additional info like tool_used, city, etc.
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id)
                )
            """)
            
            # Create travel plans table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS travel_plans (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'default',
                title TEXT NOT NULL,
                destination_data TEXT NOT NULL,  -- JSON for destination object
                dates_data TEXT NOT NULL,       -- JSON for dates object
                participants_data TEXT NOT NULL, -- JSON for participants object
                budget_data TEXT NOT NULL,      -- JSON for budget object
                requirements_data TEXT,         -- JSON for requirements object
                preferences_data TEXT,          -- JSON for preferences object
                activities_data TEXT,           -- JSON for activities object
                logistics_data TEXT,            -- JSON for logistics object
                itinerary_data TEXT,            -- JSON for itinerary array
                status_data TEXT NOT NULL,      -- JSON for status object
                emergency_contacts_data TEXT,   -- JSON for emergency contacts
                documents_data TEXT,            -- JSON for documents object
                notes TEXT,
                created_by TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversation_history_conv_id ON conversation_history (conversation_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversation_history_timestamp ON conversation_history (timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_book_car_user_date ON book_car (user_id, pickup_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_book_hotel_user_date ON book_hotel (user_id, checkin_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_travel_plans_user_id ON travel_plans (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_travel_plans_created_at ON travel_plans (created_at)")
            
            conn.commit()
    
    # ===== AGENT CONFIG METHODS =====
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get current agent configuration"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_config ORDER BY updated_at DESC LIMIT 1")
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            else:
                # Return default config if none exists
                return self._get_default_agent_config()
    
    def save_agent_config(self, config: Dict[str, Any]) -> bool:
        """Save agent configuration"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO agent_config (
                        agent_name, personality, avatar, tone, emoji_usage,
                        creativity, context_messages, show_tool_info, 
                        show_context_preview, enable_tts, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    config.get('agent_name', 'AI Travel Assistant'),
                    config.get('personality', 'friendly'),
                    config.get('avatar', '🤖'),
                    config.get('tone', 'casual'),
                    config.get('emoji_usage', 'moderate'),
                    config.get('creativity', 0.7),
                    config.get('context_messages', 5),
                    config.get('show_tool_info', True),
                    config.get('show_context_preview', True),
                    config.get('enable_tts', False)
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving agent config: {e}")
            return False
    
    # ===== PERSONALITY TEMPLATES METHODS =====
    
    def get_personality_templates(self) -> Dict[str, Any]:
        """Get all personality templates"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM personality_templates")
            rows = cursor.fetchall()
            
            if rows:
                templates = {"personalities": {}}
                for row in rows:
                    templates["personalities"][row["personality_type"]] = {
                        "description": row["description"],
                        "greeting_messages": json.loads(row["greeting_messages"]),
                        "response_style": json.loads(row["response_style"])
                    }
                return templates
            else:
                return self._get_default_personality_templates()
    
    def save_personality_template(self, personality_type: str, template: Dict[str, Any]) -> bool:
        """Save or update a personality template"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO personality_templates (
                        personality_type, description, greeting_messages, response_style
                    ) VALUES (?, ?, ?, ?)
                """, (
                    personality_type,
                    template.get('description', ''),
                    json.dumps(template.get('greeting_messages', [])),
                    json.dumps(template.get('response_style', {}))
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving personality template: {e}")
            return False
    
    # ===== USER PREFERENCES METHODS =====
    
    def get_user_preferences(self, user_id: str = 'default') -> Dict[str, Any]:
        """Get user preferences"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_preferences WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1", (user_id,))
            row = cursor.fetchone()
            
            if row:
                prefs = dict(row)
                # Parse JSON fields
                for json_field in ['travel_interests', 'dietary_restrictions', 'favorite_cuisines', 'bucket_list', 'visited_places']:
                    if prefs.get(json_field):
                        prefs[json_field] = json.loads(prefs[json_field])
                    else:
                        prefs[json_field] = []
                return prefs
            else:
                return self._get_default_user_preferences()
    
    def save_user_preferences(self, preferences: Dict[str, Any], user_id: str = 'default') -> bool:
        """Save user preferences"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_preferences (
                        user_id, travel_interests, budget_preference, dietary_restrictions,
                        favorite_cuisines, bucket_list, visited_places, remember_preferences,
                        proactive_suggestions, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    user_id,
                    json.dumps(preferences.get('travel_interests', [])),
                    preferences.get('budget_preference', 'medium'),
                    json.dumps(preferences.get('dietary_restrictions', [])),
                    json.dumps(preferences.get('favorite_cuisines', [])),
                    json.dumps(preferences.get('bucket_list', [])),
                    json.dumps(preferences.get('visited_places', [])),
                    preferences.get('remember_preferences', True),
                    preferences.get('proactive_suggestions', True)
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving user preferences: {e}")
            return False
    
    # ===== BOOKING METHODS =====
    
    def save_car_booking(self, booking: Dict[str, Any], user_id: str = 'default') -> int:
        """Save car booking and return booking ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO book_car (
                        user_id, pickup_location, dropoff_location, pickup_date, pickup_time,
                        return_date, return_time, car_type, driver_needed, passengers,
                        special_requirements, estimated_cost, booking_status, booking_reference
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    booking.get('pickup_location'),
                    booking.get('dropoff_location'),
                    booking.get('pickup_date'),
                    booking.get('pickup_time'),
                    booking.get('return_date'),
                    booking.get('return_time'),
                    booking.get('car_type'),
                    booking.get('driver_needed', False),
                    booking.get('passengers', 1),
                    booking.get('special_requirements'),
                    booking.get('estimated_cost'),
                    booking.get('booking_status', 'pending'),
                    booking.get('booking_reference')
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Error saving car booking: {e}")
            return 0
    
    def save_hotel_booking(self, booking: Dict[str, Any], user_id: str = 'default') -> int:
        """Save hotel booking and return booking ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO book_hotel (
                        user_id, hotel_name, location, checkin_date, checkout_date,
                        adults, children, room_type, room_count, budget_range,
                        amenities, special_requests, estimated_cost, booking_status,
                        booking_reference
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    booking.get('hotel_name'),
                    booking.get('location'),
                    booking.get('checkin_date'),
                    booking.get('checkout_date'),
                    booking.get('adults', 1),
                    booking.get('children', 0),
                    booking.get('room_type'),
                    booking.get('room_count', 1),
                    booking.get('budget_range'),
                    json.dumps(booking.get('amenities', [])),
                    booking.get('special_requests'),
                    booking.get('estimated_cost'),
                    booking.get('booking_status', 'pending'),
                    booking.get('booking_reference')
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Error saving hotel booking: {e}")
            return 0
    
    def get_user_bookings(self, user_id: str = 'default', booking_type: str = 'all') -> Dict[str, List]:
        """Get user bookings (car, hotel, or both)"""
        bookings = {"car_bookings": [], "hotel_bookings": []}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if booking_type in ['all', 'car']:
                cursor.execute("SELECT * FROM book_car WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
                bookings["car_bookings"] = [dict(row) for row in cursor.fetchall()]
            
            if booking_type in ['all', 'hotel']:
                cursor.execute("SELECT * FROM book_hotel WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
                hotel_rows = cursor.fetchall()
                for row in hotel_rows:
                    booking = dict(row)
                    if booking.get('amenities'):
                        booking['amenities'] = json.loads(booking['amenities'])
                    bookings["hotel_bookings"].append(booking)
        
        return bookings
    
    # ===== CONVERSATION METHODS =====
    
    def create_conversation(self, title: str, user_id: str = 'default') -> str:
        """Create new conversation and return conversation_id"""
        import uuid
        conversation_id = str(uuid.uuid4())
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Set all conversations as inactive
                cursor.execute("UPDATE conversations SET is_active = 0 WHERE user_id = ?", (user_id,))
                
                # Create new active conversation
                cursor.execute("""
                    INSERT INTO conversations (conversation_id, user_id, title, is_active)
                    VALUES (?, ?, ?, 1)
                """, (conversation_id, user_id, title))
                
                conn.commit()
                return conversation_id
        except Exception as e:
            print(f"Error creating conversation: {e}")
            return ""
    
    def get_conversations(self, user_id: str = 'default') -> List[Dict[str, Any]]:
        """Get all conversations for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM conversations 
                WHERE user_id = ? 
                ORDER BY updated_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_active_conversation(self, user_id: str = 'default') -> Optional[str]:
        """Get active conversation ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT conversation_id FROM conversations 
                WHERE user_id = ? AND is_active = 1 
                LIMIT 1
            """, (user_id,))
            row = cursor.fetchone()
            return row['conversation_id'] if row else None
    
    def set_active_conversation(self, conversation_id: str, user_id: str = 'default') -> bool:
        """Set conversation as active"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Set all conversations as inactive
                cursor.execute("UPDATE conversations SET is_active = 0 WHERE user_id = ?", (user_id,))
                
                # Set specified conversation as active
                cursor.execute("""
                    UPDATE conversations 
                    SET is_active = 1, updated_at = CURRENT_TIMESTAMP 
                    WHERE conversation_id = ? AND user_id = ?
                """, (conversation_id, user_id))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error setting active conversation: {e}")
            return False
    
    def update_conversation_title(self, conversation_id: str, new_title: str, user_id: str = 'default') -> bool:
        """Update conversation title"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE conversations 
                    SET title = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE conversation_id = ? AND user_id = ?
                """, (new_title, conversation_id, user_id))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating conversation title: {e}")
            return False
    
    def delete_conversation(self, conversation_id: str, user_id: str = 'default') -> bool:
        """Delete conversation and its history"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete conversation history first (foreign key constraint)
                cursor.execute("DELETE FROM conversation_history WHERE conversation_id = ?", (conversation_id,))
                
                # Delete conversation
                cursor.execute("DELETE FROM conversations WHERE conversation_id = ? AND user_id = ?", (conversation_id, user_id))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False
    
    def save_message(self, conversation_id: str, message_type: str, content: str, metadata: Dict = None) -> bool:
        """Save message to conversation history"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversation_history (
                        conversation_id, message_type, message_content, metadata
                    ) VALUES (?, ?, ?, ?)
                """, (
                    conversation_id,
                    message_type,
                    content,
                    json.dumps(metadata or {})
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving message: {e}")
            return False
    
    def get_conversation_history(self, conversation_id: str, limit: int = None) -> List[Tuple[str, str]]:
        """Get conversation history as (message_type, content) tuples"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT message_type, message_content, metadata, timestamp 
                FROM conversation_history 
                WHERE conversation_id = ? 
                ORDER BY timestamp ASC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (conversation_id,))
            rows = cursor.fetchall()
            
            history = []
            for row in rows:
                history.append((row['message_type'], row['message_content']))
            
            return history
    
    # ===== DEFAULT DATA METHODS =====
    
    def _get_default_agent_config(self) -> Dict[str, Any]:
        """Get default agent configuration"""
        return {
            'agent_name': 'AI Travel Assistant',
            'personality': 'friendly',
            'avatar': '🤖',
            'tone': 'casual',
            'emoji_usage': 'moderate',
            'creativity': 0.7,
            'context_messages': 5,
            'show_tool_info': True,
            'show_context_preview': True,
            'enable_tts': False
        }
    
    def _get_default_personality_templates(self) -> Dict[str, Any]:
        """Get default personality templates"""
        return {
            "personalities": {
                "friendly": {
                    "description": "Thân thiện, ấm áp và gần gũi",
                    "greeting_messages": [
                        "Xin chào! Mình là {agent_name}, trợ lý du lịch của bạn! 😊",
                        "Chào bạn! {agent_name} đây, sẵn sàng giúp bạn khám phá những chuyến đi tuyệt vời! ✈️",
                        "Hi! Mình là {agent_name}. Hãy cùng lên kế hoạch cho chuyến đi thú vị nhé! 🌟"
                    ],
                    "response_style": {
                        "tone": "warm",
                        "emoji_frequency": "high",
                        "formality": "casual"
                    }
                },
                "professional": {
                    "description": "Chuyên nghiệp, lịch sự và đáng tin cậy",
                    "greeting_messages": [
                        "Xin chào, tôi là {agent_name} - chuyên gia tư vấn du lịch của bạn.",
                        "Chào bạn, {agent_name} tại đây. Tôi sẽ hỗ trợ bạn lên kế hoạch du lịch một cách chuyên nghiệp.",
                        "Xin chào, tôi là {agent_name}. Rất hân hạnh được phục vụ bạn trong chuyến hành trình sắp tới."
                    ],
                    "response_style": {
                        "tone": "formal",
                        "emoji_frequency": "low",
                        "formality": "professional"
                    }
                },
                "enthusiastic": {
                    "description": "Năng động, nhiệt tình và đầy hứng khởi",
                    "greeting_messages": [
                        "Wow! Chào bạn! Mình là {agent_name} và mình cực kỳ hào hứng được giúp bạn khám phá thế giới! 🚀✨",
                        "Yayyy! {agent_name} đây! Sẵn sàng cho những cuộc phiêu lưu tuyệt vời chưa?! 🎉🌍",
                        "Chào bạn! Mình là {agent_name} và mình không thể chờ đợi để giúp bạn tạo ra những kỷ niệm đáng nhớ! 🌟🎊"
                    ],
                    "response_style": {
                        "tone": "energetic",
                        "emoji_frequency": "very_high",
                        "formality": "very_casual"
                    }
                },
                "local_expert": {
                    "description": "Như người bạn địa phương am hiểu sâu sắc",
                    "greeting_messages": [
                        "Chào bạn! Mình là {agent_name}. Với kinh nghiệm nhiều năm, mình sẽ chia sẻ những bí mật địa phương tuyệt vời nhất! 🗺️",
                        "Xin chào! {agent_name} đây - người bạn địa phương của bạn. Mình biết những nơi mà tourist thường bỏ lỡ đấy! 😉",
                        "Hi! Mình là {agent_name}. Hãy để mình dẫn bạn khám phá những góc khuất tuyệt đẹp như người dân địa phương! 🏘️"
                    ],
                    "response_style": {
                        "tone": "knowledgeable",
                        "emoji_frequency": "moderate",
                        "formality": "friendly_expert"
                    }
                }
            }
        }
    
    def _get_default_user_preferences(self) -> Dict[str, Any]:
        """Get default user preferences"""
        return {
            'travel_interests': [],
            'budget_preference': 'medium',
            'dietary_restrictions': [],
            'favorite_cuisines': [],
            'bucket_list': [],
            'visited_places': [],
            'remember_preferences': True,
            'proactive_suggestions': True
        }
    
    def initialize_default_data(self):
        """Initialize database with default personality templates if empty"""
        templates = self._get_default_personality_templates()
        
        for personality_type, template in templates["personalities"].items():
            self.save_personality_template(personality_type, template)
        
        print("✅ Default personality templates initialized in database")

    def get_all_car_bookings(self) -> List[Dict[str, Any]]:
        """Get all car booking records"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM book_car 
                    ORDER BY created_at DESC
                """)
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                columns = [description[0] for description in cursor.description]
                bookings = []
                for row in rows:
                    booking = dict(zip(columns, row))
                    bookings.append(booking)
                
                return bookings
        except Exception as e:
            print(f"Error getting car bookings: {e}")
            return []
    
    def get_all_hotel_bookings(self) -> List[Dict[str, Any]]:
        """Get all hotel booking records"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM book_hotel 
                    ORDER BY created_at DESC
                """)
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                columns = [description[0] for description in cursor.description]
                bookings = []
                for row in rows:
                    booking = dict(zip(columns, row))
                    bookings.append(booking)
                
                return bookings
        except Exception as e:
            print(f"Error getting hotel bookings: {e}")
            return []
    
    def update_car_booking_status(self, booking_id: str, status: str) -> bool:
        """Update car booking status"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE book_car 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (status, booking_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating car booking status: {e}")
            return False
    
    def update_hotel_booking_status(self, booking_id: str, status: str) -> bool:
        """Update hotel booking status"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE book_hotel 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (status, booking_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating hotel booking status: {e}")
            return False
    
    def delete_car_booking(self, booking_id: str) -> bool:
        """Delete a car booking"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM book_car WHERE id = ?", (booking_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting car booking: {e}")
            return False
    
    def delete_hotel_booking(self, booking_id: str) -> bool:
        """Delete a hotel booking"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM book_hotel WHERE id = ?", (booking_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting hotel booking: {e}")
            return False

    # Enhanced booking save functions with field mapping
    def save_car_booking_enhanced(self, booking_details: Dict[str, Any]) -> bool:
        """Save car booking with enhanced field mapping"""
        try:
            # Map fields from booking details to database schema
            mapped_booking = {
                'pickup_location': booking_details.get('pickup_location', ''),
                'dropoff_location': booking_details.get('destination', ''),
                'pickup_date': booking_details.get('pickup_time', '').split(' ')[0] if booking_details.get('pickup_time') else '',
                'pickup_time': booking_details.get('pickup_time', ''),
                'return_date': None,  # Not used in current flow
                'return_time': None,  # Not used in current flow
                'car_type': booking_details.get('car_type', ''),
                'driver_needed': True,  # Assume driver is always needed
                'passengers': booking_details.get('seats', 4),
                'special_requirements': booking_details.get('notes', ''),
                'estimated_cost': None,  # To be calculated by system
                'booking_status': booking_details.get('status', 'confirmed'),
                'booking_reference': booking_details.get('id', '')
            }
            
            # Save using existing method
            booking_id = self.save_car_booking(mapped_booking, 'default')
            return booking_id > 0
            
        except Exception as e:
            print(f"Error saving enhanced car booking: {e}")
            return False
    
    def save_hotel_booking_enhanced(self, booking_details: Dict[str, Any]) -> bool:
        """Save hotel booking with enhanced field mapping"""
        try:
            # Map fields from booking details to database schema
            mapped_booking = {
                'hotel_name': booking_details.get('hotel_name', ''),
                'location': booking_details.get('location', ''),
                'checkin_date': booking_details.get('check_in_date', ''),
                'checkout_date': booking_details.get('check_out_date', ''),
                'adults': booking_details.get('guests', 2),
                'children': 0,
                'room_type': booking_details.get('room_type', 'standard'),
                'room_count': booking_details.get('rooms', 1),
                'budget_range': 'mid-range',  # Default
                'amenities': '',  # Empty for now
                'special_requests': booking_details.get('special_requests', ''),
                'estimated_cost': None,  # To be calculated by system
                'booking_status': booking_details.get('status', 'confirmed'),
                'booking_reference': booking_details.get('id', '')
            }
            
            # Save using existing method
            booking_id = self.save_hotel_booking(mapped_booking, 'default')
            return booking_id > 0
            
        except Exception as e:
            print(f"Error saving enhanced hotel booking: {e}")
            return False

    # Travel Plans Management Methods
    def save_travel_plan(self, travel_plan: Dict[str, Any]) -> bool:
        """Save travel plan to database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO travel_plans (
                        id, user_id, title, destination_data, dates_data, 
                        participants_data, budget_data, requirements_data,
                        preferences_data, activities_data, logistics_data,
                        itinerary_data, status_data, emergency_contacts_data,
                        documents_data, notes, created_by, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    travel_plan['id'],
                    travel_plan.get('user_id', 'default'),
                    travel_plan['title'],
                    json.dumps(travel_plan['destination'], ensure_ascii=False),
                    json.dumps(travel_plan['dates'], ensure_ascii=False),
                    json.dumps(travel_plan['participants'], ensure_ascii=False),
                    json.dumps(travel_plan['budget'], ensure_ascii=False),
                    json.dumps(travel_plan.get('requirements', {}), ensure_ascii=False),
                    json.dumps(travel_plan.get('preferences', {}), ensure_ascii=False),
                    json.dumps(travel_plan.get('activities', {}), ensure_ascii=False),
                    json.dumps(travel_plan.get('logistics', {}), ensure_ascii=False),
                    json.dumps(travel_plan.get('itinerary', []), ensure_ascii=False),
                    json.dumps(travel_plan['status'], ensure_ascii=False),
                    json.dumps(travel_plan.get('emergency_contacts', []), ensure_ascii=False),
                    json.dumps(travel_plan.get('documents', {}), ensure_ascii=False),
                    travel_plan.get('notes', ''),
                    travel_plan.get('created_by', 'AI Assistant')
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving travel plan: {e}")
            return False
    
    def get_all_travel_plans(self, user_id: str = 'default') -> List[Dict[str, Any]]:
        """Get all travel plans for a user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM travel_plans 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,))
                rows = cursor.fetchall()
                
                plans = []
                for row in rows:
                    row_dict = dict(row)
                    # Parse JSON fields
                    try:
                        row_dict['destination'] = json.loads(row_dict['destination_data'])
                        row_dict['dates'] = json.loads(row_dict['dates_data'])
                        row_dict['participants'] = json.loads(row_dict['participants_data'])
                        row_dict['budget'] = json.loads(row_dict['budget_data'])
                        row_dict['requirements'] = json.loads(row_dict['requirements_data'] or '{}')
                        row_dict['preferences'] = json.loads(row_dict['preferences_data'] or '{}')
                        row_dict['activities'] = json.loads(row_dict['activities_data'] or '{}')
                        row_dict['logistics'] = json.loads(row_dict['logistics_data'] or '{}')
                        row_dict['itinerary'] = json.loads(row_dict['itinerary_data'] or '[]')
                        row_dict['status'] = json.loads(row_dict['status_data'])
                        row_dict['emergency_contacts'] = json.loads(row_dict['emergency_contacts_data'] or '[]')
                        row_dict['documents'] = json.loads(row_dict['documents_data'] or '{}')
                        
                        # Remove JSON string fields
                        for field in ['destination_data', 'dates_data', 'participants_data', 'budget_data', 
                                    'requirements_data', 'preferences_data', 'activities_data', 
                                    'logistics_data', 'itinerary_data', 'status_data',
                                    'emergency_contacts_data', 'documents_data']:
                            if field in row_dict:
                                del row_dict[field]
                        
                        plans.append(row_dict)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON for travel plan {row_dict['id']}: {e}")
                        continue
                
                return plans
        except Exception as e:
            print(f"Error getting travel plans: {e}")
            return []
    
    def get_travel_plan(self, plan_id: str) -> Dict[str, Any]:
        """Get a specific travel plan by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM travel_plans WHERE id = ?", (plan_id,))
                row = cursor.fetchone()
                
                if row:
                    row_dict = dict(row)
                    # Parse JSON fields
                    row_dict['destination'] = json.loads(row_dict['destination_data'])
                    row_dict['dates'] = json.loads(row_dict['dates_data'])
                    row_dict['participants'] = json.loads(row_dict['participants_data'])
                    row_dict['budget'] = json.loads(row_dict['budget_data'])
                    row_dict['requirements'] = json.loads(row_dict['requirements_data'] or '{}')
                    row_dict['preferences'] = json.loads(row_dict['preferences_data'] or '{}')
                    row_dict['activities'] = json.loads(row_dict['activities_data'] or '{}')
                    row_dict['logistics'] = json.loads(row_dict['logistics_data'] or '{}')
                    row_dict['itinerary'] = json.loads(row_dict['itinerary_data'] or '[]')
                    row_dict['status'] = json.loads(row_dict['status_data'])
                    row_dict['emergency_contacts'] = json.loads(row_dict['emergency_contacts_data'] or '[]')
                    row_dict['documents'] = json.loads(row_dict['documents_data'] or '{}')
                    
                    # Remove JSON string fields
                    for field in ['destination_data', 'dates_data', 'participants_data', 'budget_data', 
                                'requirements_data', 'preferences_data', 'activities_data', 
                                'logistics_data', 'itinerary_data', 'status_data',
                                'emergency_contacts_data', 'documents_data']:
                        if field in row_dict:
                            del row_dict[field]
                    
                    return row_dict
                return {}
        except Exception as e:
            print(f"Error getting travel plan: {e}")
            return {}
    
    def delete_travel_plan(self, plan_id: str) -> bool:
        """Delete a travel plan"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM travel_plans WHERE id = ?", (plan_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting travel plan: {e}")
            return False
    
    def update_travel_plan_status(self, plan_id: str, status: str, progress: int = None) -> bool:
        """Update travel plan status"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get current status data
                cursor.execute("SELECT status_data FROM travel_plans WHERE id = ?", (plan_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                
                status_data = json.loads(row['status_data'])
                status_data['current_status'] = status
                if progress is not None:
                    status_data['progress_percentage'] = progress
                status_data['last_updated'] = datetime.now().isoformat()
                
                cursor.execute("""
                    UPDATE travel_plans 
                    SET status_data = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (json.dumps(status_data, ensure_ascii=False), plan_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating travel plan status: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Test the database manager
    db = DatabaseManager()
    
    # Initialize default data
    db.initialize_default_data()
    
    # Test agent config
    config = {
        'agent_name': 'Mai',
        'personality': 'friendly',
        'creativity': 0.8
    }
    db.save_agent_config(config)
    
    print("Agent config:", db.get_agent_config())
    print("Personality templates:", db.get_personality_templates())