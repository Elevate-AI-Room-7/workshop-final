"""
Suggestion Engine - Generate contextual relation questions/prompts
Based on user interactions, tool usage, and RAG results
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ToolType(Enum):
    """Enum for different tool types"""
    RAG = "RAG"
    WEATHER = "WEATHER"
    HOTEL = "HOTEL"
    CAR = "CAR"
    TRAVEL_PLAN = "TRAVEL_PLAN"
    GENERAL = "GENERAL"


@dataclass
class SuggestionContext:
    """Context data for generating suggestions"""
    tool_used: ToolType
    user_query: str
    agent_response: str
    location: Optional[str] = None
    rag_sources: Optional[List[Dict]] = None
    booking_details: Optional[Dict] = None
    chat_history: Optional[List[Tuple[str, str]]] = None
    user_interests: Optional[List[str]] = None


@dataclass
class Suggestion:
    """A single suggestion with metadata"""
    text: str
    category: str
    tool_target: ToolType
    priority: float
    context_relevance: float
    
    def total_score(self) -> float:
        """Calculate total relevance score"""
        return (self.priority * 0.6) + (self.context_relevance * 0.4)


class SuggestionEngine:
    """
    Main engine for generating contextual suggestions based on user interactions
    """
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.suggestion_templates = self._load_suggestion_templates()
        
        # Configuration from ConfigManager or defaults
        if self.config_manager:
            self.max_suggestions = self.config_manager.get_max_suggestions()
            self.min_relevance_score = self.config_manager.get_suggestion_min_score()
            self.diversity_factor = self.config_manager.get_suggestion_diversity_factor()
        else:
            # Default configuration
            self.max_suggestions = 5
            self.min_relevance_score = 0.3
            self.diversity_factor = 0.7  # Higher = more diverse suggestions
        
    def generate_suggestions(self, context: SuggestionContext) -> List[Suggestion]:
        """
        Main method to generate contextual suggestions
        
        Args:
            context: SuggestionContext with user interaction data
            
        Returns:
            List of relevant suggestions sorted by score
        """
        try:
            # Check if suggestions are enabled
            if self.config_manager and not self.config_manager.get_suggestion_enabled():
                return []
            
            # Step 1: Generate candidate suggestions based on tool used
            candidates = self._generate_candidates_by_tool(context)
            
            # Step 2: Add cross-tool suggestions if enabled
            if not self.config_manager or self.config_manager.should_show_cross_tool_suggestions():
                candidates.extend(self._generate_cross_tool_suggestions(context))
            
            # Step 3: Add location-based suggestions if location available and enabled
            if context.location and (not self.config_manager or self.config_manager.should_show_location_suggestions()):
                candidates.extend(self._generate_location_suggestions(context))
            
            # Step 4: Add RAG-based suggestions if RAG sources available and enabled
            if context.rag_sources and (not self.config_manager or self.config_manager.should_show_rag_suggestions()):
                candidates.extend(self._generate_rag_suggestions(context))
            
            # Step 5: Filter and score suggestions
            filtered_suggestions = self._filter_and_score(candidates, context)
            
            # Step 6: Apply diversity and select top suggestions
            final_suggestions = self._apply_diversity_selection(filtered_suggestions)
            
            return final_suggestions[:self.max_suggestions]
            
        except Exception as e:
            print(f"Error generating suggestions: {str(e)}")
            return []
    
    def _generate_candidates_by_tool(self, context: SuggestionContext) -> List[Suggestion]:
        """Generate suggestions based on the tool that was used"""
        candidates = []
        tool = context.tool_used
        
        if tool == ToolType.RAG:
            candidates.extend(self._generate_rag_tool_suggestions(context))
        elif tool == ToolType.WEATHER:
            candidates.extend(self._generate_weather_tool_suggestions(context))
        elif tool == ToolType.HOTEL:
            candidates.extend(self._generate_hotel_tool_suggestions(context))
        elif tool == ToolType.CAR:
            candidates.extend(self._generate_car_tool_suggestions(context))
        elif tool == ToolType.TRAVEL_PLAN:
            candidates.extend(self._generate_travel_plan_tool_suggestions(context))
        elif tool == ToolType.GENERAL:
            candidates.extend(self._generate_general_tool_suggestions(context))
            
        return candidates
    
    def _generate_rag_tool_suggestions(self, context: SuggestionContext) -> List[Suggestion]:
        """Generate suggestions when RAG tool was used"""
        suggestions = []
        location = context.location or self._extract_location_from_text(context.user_query)
        
        templates = self.suggestion_templates["rag_tool"]
        
        for template in templates:
            suggestion_text = template["text"].format(location=location or "địa điểm này")
            suggestions.append(Suggestion(
                text=suggestion_text,
                category=template["category"],
                tool_target=ToolType(template["tool_target"]),
                priority=template["priority"],
                context_relevance=self._calculate_context_relevance(template, context)
            ))
        
        return suggestions
    
    def _generate_weather_tool_suggestions(self, context: SuggestionContext) -> List[Suggestion]:
        """Generate suggestions when Weather tool was used"""
        suggestions = []
        location = context.location or self._extract_location_from_text(context.user_query)
        
        templates = self.suggestion_templates["weather_tool"]
        
        for template in templates:
            suggestion_text = template["text"].format(location=location or "địa điểm này")
            suggestions.append(Suggestion(
                text=suggestion_text,
                category=template["category"],
                tool_target=ToolType(template["tool_target"]),
                priority=template["priority"],
                context_relevance=self._calculate_context_relevance(template, context)
            ))
        
        return suggestions
    
    def _generate_hotel_tool_suggestions(self, context: SuggestionContext) -> List[Suggestion]:
        """Generate suggestions when Hotel booking tool was used"""
        suggestions = []
        location = context.location or self._extract_location_from_text(context.user_query)
        
        templates = self.suggestion_templates["hotel_tool"]
        
        for template in templates:
            suggestion_text = template["text"].format(location=location or "địa điểm này")
            suggestions.append(Suggestion(
                text=suggestion_text,
                category=template["category"],
                tool_target=ToolType(template["tool_target"]),
                priority=template["priority"],
                context_relevance=self._calculate_context_relevance(template, context)
            ))
        
        return suggestions
    
    def _generate_car_tool_suggestions(self, context: SuggestionContext) -> List[Suggestion]:
        """Generate suggestions when Car booking tool was used"""
        suggestions = []
        location = context.location or self._extract_location_from_text(context.user_query)
        
        templates = self.suggestion_templates["car_tool"]
        
        for template in templates:
            suggestion_text = template["text"].format(location=location or "địa điểm này")
            suggestions.append(Suggestion(
                text=suggestion_text,
                category=template["category"],
                tool_target=ToolType(template["tool_target"]),
                priority=template["priority"],
                context_relevance=self._calculate_context_relevance(template, context)
            ))
        
        return suggestions
    
    def _generate_travel_plan_tool_suggestions(self, context: SuggestionContext) -> List[Suggestion]:
        """Generate suggestions when Travel Planning tool was used"""
        suggestions = []
        location = context.location or self._extract_location_from_text(context.user_query)
        
        templates = self.suggestion_templates["travel_plan_tool"]
        
        for template in templates:
            suggestion_text = template["text"].format(location=location or "địa điểm này")
            suggestions.append(Suggestion(
                text=suggestion_text,
                category=template["category"],
                tool_target=ToolType(template["tool_target"]),
                priority=template["priority"],
                context_relevance=self._calculate_context_relevance(template, context)
            ))
        
        return suggestions
    
    def _generate_general_tool_suggestions(self, context: SuggestionContext) -> List[Suggestion]:
        """Generate suggestions when General chat was used"""
        suggestions = []
        
        # Analyze conversation for travel intent
        travel_keywords = ["du lịch", "travel", "đi chơi", "nghỉ dưỡng", "kỳ nghỉ"]
        has_travel_intent = any(keyword in context.user_query.lower() for keyword in travel_keywords)
        
        if has_travel_intent:
            templates = self.suggestion_templates["general_travel"]
        else:
            templates = self.suggestion_templates["general_chat"]
        
        for template in templates:
            suggestions.append(Suggestion(
                text=template["text"],
                category=template["category"],
                tool_target=ToolType(template["tool_target"]),
                priority=template["priority"],
                context_relevance=self._calculate_context_relevance(template, context)
            ))
        
        return suggestions
    
    def _generate_cross_tool_suggestions(self, context: SuggestionContext) -> List[Suggestion]:
        """Generate cross-tool suggestions based on natural flow"""
        suggestions = []
        
        # Define natural flow paths
        flow_patterns = {
            ToolType.RAG: [ToolType.WEATHER, ToolType.HOTEL, ToolType.TRAVEL_PLAN],
            ToolType.WEATHER: [ToolType.HOTEL, ToolType.CAR, ToolType.TRAVEL_PLAN],
            ToolType.HOTEL: [ToolType.CAR, ToolType.RAG, ToolType.WEATHER],
            ToolType.CAR: [ToolType.HOTEL, ToolType.RAG, ToolType.WEATHER],
            ToolType.TRAVEL_PLAN: [ToolType.HOTEL, ToolType.CAR, ToolType.WEATHER],
            ToolType.GENERAL: [ToolType.RAG, ToolType.WEATHER, ToolType.TRAVEL_PLAN]
        }
        
        next_tools = flow_patterns.get(context.tool_used, [])
        location = context.location or self._extract_location_from_text(context.user_query)
        
        for next_tool in next_tools:
            templates = self.suggestion_templates["cross_tool"].get(next_tool.value, [])
            for template in templates[:2]:  # Limit to 2 per tool
                suggestion_text = template["text"].format(location=location or "địa điểm này")
                suggestions.append(Suggestion(
                    text=suggestion_text,
                    category="cross_tool",
                    tool_target=next_tool,
                    priority=template["priority"] * 0.8,  # Slightly lower priority for cross-tool
                    context_relevance=self._calculate_context_relevance(template, context)
                ))
        
        return suggestions
    
    def _generate_location_suggestions(self, context: SuggestionContext) -> List[Suggestion]:
        """Generate location-specific suggestions"""
        suggestions = []
        location = context.location
        
        # Get location-specific templates
        location_templates = self.suggestion_templates["location_specific"]
        
        # Check if we have specific templates for this location
        location_lower = location.lower()
        location_key = None
        
        for key in location_templates.keys():
            if key.lower() in location_lower or location_lower in key.lower():
                location_key = key
                break
        
        if location_key:
            templates = location_templates[location_key]
            for template in templates:
                suggestion_text = template["text"].format(location=location)
                suggestions.append(Suggestion(
                    text=suggestion_text,
                    category="location_specific",
                    tool_target=ToolType(template["tool_target"]),
                    priority=template["priority"],
                    context_relevance=self._calculate_context_relevance(template, context) + 0.2  # Boost for location match
                ))
        
        return suggestions
    
    def _generate_rag_suggestions(self, context: SuggestionContext) -> List[Suggestion]:
        """Generate suggestions based on RAG sources/chunks"""
        suggestions = []
        
        if not context.rag_sources:
            return suggestions
        
        # Analyze RAG sources for categories and related topics
        categories_found = set()
        locations_found = set()
        
        for source in context.rag_sources:
            if isinstance(source, dict):
                # Extract category from metadata
                category = source.get('category', '')
                if category:
                    categories_found.add(category)
                
                # Extract location from metadata
                location = source.get('location', '')
                if location:
                    locations_found.add(location)
        
        # Generate suggestions based on found categories
        rag_templates = self.suggestion_templates["rag_based"]
        
        for category in categories_found:
            if category in rag_templates:
                templates = rag_templates[category]
                for template in templates:
                    location = context.location or list(locations_found)[0] if locations_found else "địa điểm này"
                    suggestion_text = template["text"].format(location=location)
                    suggestions.append(Suggestion(
                        text=suggestion_text,
                        category=f"rag_{category}",
                        tool_target=ToolType(template["tool_target"]),
                        priority=template["priority"],
                        context_relevance=self._calculate_context_relevance(template, context) + 0.3  # High boost for RAG match
                    ))
        
        return suggestions
    
    def _calculate_context_relevance(self, template: Dict, context: SuggestionContext) -> float:
        """Calculate how relevant a template is to the current context"""
        relevance = 0.5  # Base relevance
        
        # Check keyword matches
        keywords = template.get("keywords", [])
        if keywords:
            text_to_check = (context.user_query + " " + context.agent_response).lower()
            matches = sum(1 for keyword in keywords if keyword.lower() in text_to_check)
            relevance += (matches / len(keywords)) * 0.3
        
        # Check user interests
        if context.user_interests and template.get("interests"):
            template_interests = template["interests"]
            interest_matches = sum(1 for interest in template_interests if interest in context.user_interests)
            if template_interests:
                relevance += (interest_matches / len(template_interests)) * 0.2
        
        # Check location relevance
        if context.location and template.get("location_relevant", True):
            relevance += 0.1
        
        return min(relevance, 1.0)  # Cap at 1.0
    
    def _filter_and_score(self, candidates: List[Suggestion], context: SuggestionContext) -> List[Suggestion]:
        """Filter suggestions by relevance and remove duplicates"""
        # Remove duplicates by text
        seen_texts = set()
        unique_candidates = []
        
        for suggestion in candidates:
            if suggestion.text not in seen_texts:
                seen_texts.add(suggestion.text)
                unique_candidates.append(suggestion)
        
        # Filter by minimum relevance score
        filtered = [s for s in unique_candidates if s.total_score() >= self.min_relevance_score]
        
        # Sort by total score (descending)
        filtered.sort(key=lambda s: s.total_score(), reverse=True)
        
        return filtered
    
    def _apply_diversity_selection(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """Apply diversity to avoid too many suggestions of the same category"""
        if not suggestions:
            return []
        
        selected = []
        category_counts = {}
        tool_counts = {}
        
        for suggestion in suggestions:
            category = suggestion.category
            tool = suggestion.tool_target
            
            # Count how many we already have of this category/tool
            cat_count = category_counts.get(category, 0)
            tool_count = tool_counts.get(tool, 0)
            
            # Diversity penalty (higher counts = lower priority)
            diversity_penalty = (cat_count * 0.1) + (tool_count * 0.15)
            adjusted_score = suggestion.total_score() - diversity_penalty
            
            # Still select if score is reasonable or we have few suggestions
            if adjusted_score >= self.min_relevance_score * self.diversity_factor or len(selected) < 3:
                selected.append(suggestion)
                category_counts[category] = cat_count + 1
                tool_counts[tool] = tool_count + 1
                
                # Stop if we have enough
                if len(selected) >= self.max_suggestions:
                    break
        
        return selected
    
    def _extract_location_from_text(self, text: str) -> Optional[str]:
        """Extract location from text using simple pattern matching"""
        # Vietnamese location patterns
        vietnam_locations = [
            "hà nội", "hồ chí minh", "đà nẵng", "nha trang", "huế", "hội an",
            "sapa", "đà lạt", "phú quốc", "cần thơ", "vũng tầu", "phan thiết",
            "hạ long", "ninh bình", "mù cang chải", "tam cốc", "bái đính"
        ]
        
        text_lower = text.lower()
        for location in vietnam_locations:
            if location in text_lower:
                return location.title()
        
        return None
    
    def _load_suggestion_templates(self) -> Dict:
        """Load suggestion templates from configuration"""
        # Try to load from ConfigManager first
        if self.config_manager:
            custom_templates = self.config_manager.get_suggestion_templates_config()
            if custom_templates:
                return custom_templates
        
        # Return default templates if no custom configuration
        return {
            "rag_tool": [
                {
                    "text": "Thời tiết {location} như thế nào?",
                    "category": "weather_followup",
                    "tool_target": "WEATHER",
                    "priority": 0.8,
                    "keywords": ["địa điểm", "tham quan"],
                    "interests": ["weather"]
                },
                {
                    "text": "Đặt khách sạn gần {location}",
                    "category": "accommodation",
                    "tool_target": "HOTEL",
                    "priority": 0.9,
                    "keywords": ["khách sạn", "lưu trú"],
                    "interests": ["accommodation"]
                },
                {
                    "text": "Lên kế hoạch du lịch {location}",
                    "category": "planning",
                    "tool_target": "TRAVEL_PLAN",
                    "priority": 0.7,
                    "keywords": ["kế hoạch", "lịch trình"],
                    "interests": ["planning"]
                },
                {
                    "text": "Thuê xe di chuyển tại {location}",
                    "category": "transportation",
                    "tool_target": "CAR",
                    "priority": 0.6,
                    "keywords": ["di chuyển", "transportation"],
                    "interests": ["transportation"]
                }
            ],
            "weather_tool": [
                {
                    "text": "Đặt khách sạn ở {location}",
                    "category": "accommodation",
                    "tool_target": "HOTEL",
                    "priority": 0.8,
                    "keywords": ["đặt phòng", "lưu trú"],
                    "interests": ["accommodation"]
                },
                {
                    "text": "Thuê xe du lịch {location}",
                    "category": "transportation",
                    "tool_target": "CAR",
                    "priority": 0.7,
                    "keywords": ["thuê xe", "di chuyển"],
                    "interests": ["transportation"]
                },
                {
                    "text": "Địa điểm du lịch ở {location}",
                    "category": "attractions",
                    "tool_target": "RAG",
                    "priority": 0.9,
                    "keywords": ["địa điểm", "tham quan"],
                    "interests": ["sightseeing"]
                },
                {
                    "text": "Lên kế hoạch du lịch {location}",
                    "category": "planning",
                    "tool_target": "TRAVEL_PLAN",
                    "priority": 0.6,
                    "keywords": ["kế hoạch", "lịch trình"],
                    "interests": ["planning"]
                }
            ],
            "hotel_tool": [
                {
                    "text": "Thuê xe từ khách sạn",
                    "category": "transportation",
                    "tool_target": "CAR",
                    "priority": 0.9,
                    "keywords": ["thuê xe", "di chuyển"],
                    "interests": ["transportation"]
                },
                {
                    "text": "Thời tiết {location} ngày mai",
                    "category": "weather",
                    "tool_target": "WEATHER",
                    "priority": 0.7,
                    "keywords": ["thời tiết", "dự báo"],
                    "interests": ["weather"]
                },
                {
                    "text": "Địa điểm gần khách sạn",
                    "category": "attractions",
                    "tool_target": "RAG",
                    "priority": 0.8,
                    "keywords": ["địa điểm", "gần đây"],
                    "interests": ["sightseeing"]
                },
                {
                    "text": "Ẩm thực địa phương ở {location}",
                    "category": "food",
                    "tool_target": "RAG",
                    "priority": 0.7,
                    "keywords": ["ẩm thực", "món ăn"],
                    "interests": ["food"]
                }
            ],
            "car_tool": [
                {
                    "text": "Đặt khách sạn ở điểm đến",
                    "category": "accommodation",
                    "tool_target": "HOTEL",
                    "priority": 0.8,
                    "keywords": ["đặt phòng", "lưu trú"],
                    "interests": ["accommodation"]
                },
                {
                    "text": "Địa điểm du lịch trên đường",
                    "category": "attractions",
                    "tool_target": "RAG",
                    "priority": 0.7,
                    "keywords": ["địa điểm", "trên đường"],
                    "interests": ["sightseeing"]
                },
                {
                    "text": "Thời tiết tại điểm đến",
                    "category": "weather",
                    "tool_target": "WEATHER",
                    "priority": 0.6,
                    "keywords": ["thời tiết", "điểm đến"],
                    "interests": ["weather"]
                },
                {
                    "text": "Lên lịch trình chi tiết",
                    "category": "planning",
                    "tool_target": "TRAVEL_PLAN",
                    "priority": 0.5,
                    "keywords": ["lịch trình", "kế hoạch"],
                    "interests": ["planning"]
                }
            ],
            "travel_plan_tool": [
                {
                    "text": "Đặt khách sạn cho chuyến đi",
                    "category": "accommodation",
                    "tool_target": "HOTEL",
                    "priority": 0.9,
                    "keywords": ["đặt phòng", "khách sạn"],
                    "interests": ["accommodation"]
                },
                {
                    "text": "Đặt xe cho chuyến đi",
                    "category": "transportation",
                    "tool_target": "CAR",
                    "priority": 0.8,
                    "keywords": ["đặt xe", "transportation"],
                    "interests": ["transportation"]
                },
                {
                    "text": "Kiểm tra thời tiết các ngày",
                    "category": "weather",
                    "tool_target": "WEATHER",
                    "priority": 0.7,
                    "keywords": ["thời tiết", "dự báo"],
                    "interests": ["weather"]
                },
                {
                    "text": "Tìm hiểu thêm về địa điểm",
                    "category": "attractions",
                    "tool_target": "RAG",
                    "priority": 0.6,
                    "keywords": ["địa điểm", "thông tin"],
                    "interests": ["sightseeing"]
                }
            ],
            "general_travel": [
                {
                    "text": "Gợi ý điểm du lịch hot",
                    "category": "discovery",
                    "tool_target": "RAG",
                    "priority": 0.8,
                    "keywords": ["gợi ý", "điểm du lịch"],
                    "interests": ["sightseeing"]
                },
                {
                    "text": "Kiểm tra thời tiết hiện tại",
                    "category": "weather",
                    "tool_target": "WEATHER",
                    "priority": 0.6,
                    "keywords": ["thời tiết"],
                    "interests": ["weather"]
                },
                {
                    "text": "Lên kế hoạch du lịch",
                    "category": "planning",
                    "tool_target": "TRAVEL_PLAN",
                    "priority": 0.7,
                    "keywords": ["kế hoạch", "du lịch"],
                    "interests": ["planning"]
                }
            ],
            "general_chat": [
                {
                    "text": "Khám phá điểm du lịch Việt Nam",
                    "category": "discovery",
                    "tool_target": "RAG",
                    "priority": 0.5,
                    "keywords": ["khám phá", "du lịch"],
                    "interests": ["sightseeing"]
                },
                {
                    "text": "Tìm hiểu về du lịch",
                    "category": "info",
                    "tool_target": "RAG",
                    "priority": 0.4,
                    "keywords": ["tìm hiểu", "du lịch"],
                    "interests": ["general"]
                }
            ],
            "cross_tool": {
                "WEATHER": [
                    {
                        "text": "Thời tiết {location} hiện tại",
                        "priority": 0.7,
                        "keywords": ["thời tiết"]
                    }
                ],
                "HOTEL": [
                    {
                        "text": "Đặt phòng tại {location}",
                        "priority": 0.8,
                        "keywords": ["đặt phòng"]
                    }
                ],
                "CAR": [
                    {
                        "text": "Thuê xe tại {location}",
                        "priority": 0.7,
                        "keywords": ["thuê xe"]
                    }
                ],
                "RAG": [
                    {
                        "text": "Khám phá {location}",
                        "priority": 0.8,
                        "keywords": ["khám phá"]
                    }
                ],
                "TRAVEL_PLAN": [
                    {
                        "text": "Lên kế hoạch du lịch {location}",
                        "priority": 0.6,
                        "keywords": ["kế hoạch"]
                    }
                ]
            },
            "location_specific": {
                "Hà Nội": [
                    {
                        "text": "Thăm Hồ Hoàn Kiếm và phố cổ",
                        "tool_target": "RAG",
                        "priority": 0.9,
                        "keywords": ["hồ hoàn kiếm", "phố cổ"]
                    },
                    {
                        "text": "Ẩm thực phở Hà Nội",
                        "tool_target": "RAG",
                        "priority": 0.8,
                        "keywords": ["phở", "ẩm thực"]
                    }
                ],
                "Hồ Chí Minh": [
                    {
                        "text": "Khám phá Quận 1 và Bến Thành",
                        "tool_target": "RAG",
                        "priority": 0.9,
                        "keywords": ["quận 1", "bến thành"]
                    },
                    {
                        "text": "Ẩm thực Sài Gòn đậm đà",
                        "tool_target": "RAG",
                        "priority": 0.8,
                        "keywords": ["ẩm thực", "sài gòn"]
                    }
                ]
            },
            "rag_based": {
                "attraction": [
                    {
                        "text": "Lên lịch tham quan {location}",
                        "tool_target": "TRAVEL_PLAN",
                        "priority": 0.8,
                        "keywords": ["lịch trình", "tham quan"]
                    },
                    {
                        "text": "Đặt khách sạn gần {location}",
                        "tool_target": "HOTEL",
                        "priority": 0.7,
                        "keywords": ["khách sạn", "gần"]
                    }
                ],
                "food": [
                    {
                        "text": "Nhà hàng tốt ở {location}",
                        "tool_target": "RAG",
                        "priority": 0.7,
                        "keywords": ["nhà hàng", "ăn uống"]
                    },
                    {
                        "text": "Tour ẩm thực {location}",
                        "tool_target": "TRAVEL_PLAN",
                        "priority": 0.6,
                        "keywords": ["tour", "ẩm thực"]
                    }
                ],
                "hotel": [
                    {
                        "text": "So sánh giá khách sạn",
                        "tool_target": "HOTEL",
                        "priority": 0.8,
                        "keywords": ["so sánh", "giá"]
                    },
                    {
                        "text": "Thuê xe từ khách sạn",
                        "tool_target": "CAR",
                        "priority": 0.7,
                        "keywords": ["thuê xe", "khách sạn"]
                    }
                ]
            }
        }