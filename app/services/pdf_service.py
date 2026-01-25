"""
PDF Service.

Generates PDF documents for:
- Daily Practice Problems (DPP)
- Session Notes

Uses ReportLab for PDF generation and Gemini for content creation.
"""
import io
import logging
from typing import Dict, Any, List
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from langchain_core.messages import HumanMessage, SystemMessage
from app.core.llm_factory import get_tutor_llm

logger = logging.getLogger(__name__)


class PDFService:
    """Service for generating PDF documents."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#8b5cf6'),
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#6b7280'),
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#1f2937'),
        ))
        
        self.styles.add(ParagraphStyle(
            name='QuestionStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceBefore=15,
            spaceAfter=5,
            leftIndent=20,
            textColor=colors.HexColor('#1f2937'),
        ))
        
        self.styles.add(ParagraphStyle(
            name='AnswerStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceBefore=5,
            spaceAfter=10,
            leftIndent=40,
            textColor=colors.HexColor('#059669'),
        ))
        
        self.styles.add(ParagraphStyle(
            name='NoteContent',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceBefore=5,
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            leading=16,
        ))
        
        self.styles.add(ParagraphStyle(
            name='BulletPoint',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceBefore=3,
            spaceAfter=3,
            leftIndent=30,
            bulletIndent=15,
        ))

    async def generate_dpp(
        self,
        session: Dict[str, Any],
        day: int,
    ) -> bytes:
        """
        Generate Daily Practice Problems PDF for a specific day.
        
        Args:
            session: Session document
            day: Day number
            
        Returns:
            PDF bytes
        """
        lesson_plan = session.get("lesson_plan", {})
        days = lesson_plan.get("days", [])
        
        if day < 1 or day > len(days):
            raise ValueError(f"Invalid day: {day}")
        
        day_content = days[day - 1]
        topics = day_content.get("topics", [])
        
        # Generate questions using LLM
        questions = await self._generate_dpp_questions(
            topic=session["topic"],
            day=day,
            day_title=day_content.get("title", f"Day {day}"),
            topics=topics,
        )
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50,
        )
        
        story = []
        
        # Title
        story.append(Paragraph(
            f"Daily Practice Problems",
            self.styles['CustomTitle']
        ))
        
        story.append(Paragraph(
            f"{session['topic']} - Day {day}: {day_content.get('title', '')}",
            self.styles['SubTitle']
        ))
        
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y')}",
            self.styles['SubTitle']
        ))
        
        story.append(Spacer(1, 30))
        
        # Instructions
        story.append(Paragraph("Instructions:", self.styles['SectionHeader']))
        story.append(Paragraph(
            "• Answer all questions to reinforce your understanding of today's topics.",
            self.styles['BulletPoint']
        ))
        story.append(Paragraph(
            "• Try to solve each problem before looking at the answer.",
            self.styles['BulletPoint']
        ))
        story.append(Paragraph(
            "• Answers are provided at the end of this document.",
            self.styles['BulletPoint']
        ))
        
        story.append(Spacer(1, 20))
        
        # Questions Section
        story.append(Paragraph("Questions:", self.styles['SectionHeader']))
        
        for i, q in enumerate(questions, 1):
            story.append(Paragraph(
                f"<b>Q{i}.</b> {q['question']}",
                self.styles['QuestionStyle']
            ))
            story.append(Spacer(1, 30))  # Space for answer
        
        # Page break before answers
        story.append(PageBreak())
        
        # Answers Section
        story.append(Paragraph("Answer Key:", self.styles['SectionHeader']))
        
        for i, q in enumerate(questions, 1):
            story.append(Paragraph(
                f"<b>Q{i}.</b> {q['question']}",
                self.styles['QuestionStyle']
            ))
            story.append(Paragraph(
                f"<b>Answer:</b> {q['answer']}",
                self.styles['AnswerStyle']
            ))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    async def generate_notes(
        self,
        session: Dict[str, Any],
        day: int,
    ) -> bytes:
        """
        Generate comprehensive notes PDF for a specific day.
        
        Args:
            session: Session document
            day: Day number
            
        Returns:
            PDF bytes
        """
        lesson_plan = session.get("lesson_plan", {})
        days = lesson_plan.get("days", [])
        
        if day < 1 or day > len(days):
            raise ValueError(f"Invalid day: {day}")
        
        day_content = days[day - 1]
        topics = day_content.get("topics", [])
        
        # Generate notes using LLM
        notes = await self._generate_notes_content(
            topic=session["topic"],
            day=day,
            day_title=day_content.get("title", f"Day {day}"),
            topics=topics,
        )
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50,
        )
        
        story = []
        
        # Title
        story.append(Paragraph(
            f"Study Notes",
            self.styles['CustomTitle']
        ))
        
        story.append(Paragraph(
            f"{session['topic']} - Day {day}: {day_content.get('title', '')}",
            self.styles['SubTitle']
        ))
        
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y')}",
            self.styles['SubTitle']
        ))
        
        story.append(Spacer(1, 20))
        
        # Objectives
        objectives = day_content.get("objectives", [])
        if objectives:
            story.append(Paragraph("Learning Objectives:", self.styles['SectionHeader']))
            for obj in objectives:
                story.append(Paragraph(f"• {obj}", self.styles['BulletPoint']))
            story.append(Spacer(1, 15))
        
        # Notes content for each topic
        for topic_notes in notes:
            story.append(Paragraph(
                topic_notes['title'],
                self.styles['SectionHeader']
            ))
            
            # Split content into paragraphs
            paragraphs = topic_notes['content'].split('\n\n')
            for para in paragraphs:
                if para.strip():
                    # Handle bullet points
                    if para.strip().startswith('•') or para.strip().startswith('-'):
                        lines = para.strip().split('\n')
                        for line in lines:
                            line = line.strip()
                            if line.startswith('•') or line.startswith('-'):
                                story.append(Paragraph(line, self.styles['BulletPoint']))
                            elif line:
                                story.append(Paragraph(line, self.styles['NoteContent']))
                    else:
                        story.append(Paragraph(para.strip(), self.styles['NoteContent']))
            
            story.append(Spacer(1, 10))
        
        # Key Takeaways
        story.append(Paragraph("Key Takeaways:", self.styles['SectionHeader']))
        for topic_notes in notes:
            if topic_notes.get('key_points'):
                for point in topic_notes['key_points']:
                    story.append(Paragraph(f"• {point}", self.styles['BulletPoint']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    async def _generate_dpp_questions(
        self,
        topic: str,
        day: int,
        day_title: str,
        topics: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """Generate practice questions using LLM."""
        
        topics_str = "\n".join([
            f"- {t.get('title', 'Topic')}: {t.get('description', '')}"
            for t in topics
        ])
        
        llm = get_tutor_llm(temperature=0.7, streaming=False)
        
        prompt = f"""Generate 10 practice questions for a student who has just completed learning the following:

MAIN TOPIC: {topic}
DAY {day}: {day_title}

TOPICS COVERED:
{topics_str}

Create a mix of:
- 3 Multiple Choice Questions (with 4 options each)
- 3 Short Answer Questions
- 2 True/False Questions
- 2 Application/Problem-Solving Questions

For each question, provide:
1. The question
2. The correct answer (for MCQ, include the correct option letter)

Format your response as a JSON array like this:
[
  {{"question": "What is...?", "answer": "The answer is..."}},
  {{"question": "True or False: ...", "answer": "True/False because..."}},
  ...
]

Make questions progressively challenging and relevant to the day's content."""

        try:
            messages = [
                SystemMessage(content="You are an expert educator creating practice problems. Return ONLY valid JSON array."),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.ainvoke(messages)
            content = response.content.strip()
            
            # Parse JSON from response
            import json
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            questions = json.loads(content.strip())
            return questions[:10]  # Limit to 10 questions
            
        except Exception as e:
            logger.error(f"Error generating DPP questions: {e}")
            # Return fallback questions
            return [
                {"question": f"Explain the main concept of {day_title}.", "answer": "Review your notes for the complete answer."},
                {"question": f"What are the key takeaways from Day {day}?", "answer": "Review your notes for the complete answer."},
                {"question": f"How would you apply what you learned about {topic} today?", "answer": "Review your notes for the complete answer."},
            ]

    async def _generate_notes_content(
        self,
        topic: str,
        day: int,
        day_title: str,
        topics: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate comprehensive notes using LLM."""
        
        notes = []
        llm = get_tutor_llm(temperature=0.5, streaming=False)
        
        for t in topics:
            topic_title = t.get('title', 'Topic')
            topic_desc = t.get('description', '')
            
            prompt = f"""Create comprehensive study notes for the following topic:

MAIN SUBJECT: {topic}
DAY {day}: {day_title}
CURRENT TOPIC: {topic_title}
DESCRIPTION: {topic_desc}

Generate detailed notes that include:
1. Clear explanation of the concept
2. Important definitions
3. Examples where applicable
4. Key formulas or rules (if any)
5. Common mistakes to avoid

Keep the content educational and easy to understand. Use bullet points where appropriate.

Also provide 3-5 key takeaways at the end.

Format your response as JSON:
{{
  "content": "Your detailed notes here...",
  "key_points": ["Point 1", "Point 2", "Point 3"]
}}"""

            try:
                messages = [
                    SystemMessage(content="You are an expert educator creating study notes. Return ONLY valid JSON."),
                    HumanMessage(content=prompt)
                ]
                
                response = await llm.ainvoke(messages)
                content = response.content.strip()
                
                # Parse JSON
                import json
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                note_data = json.loads(content.strip())
                notes.append({
                    "title": topic_title,
                    "content": note_data.get("content", topic_desc),
                    "key_points": note_data.get("key_points", []),
                })
                
            except Exception as e:
                logger.error(f"Error generating notes for {topic_title}: {e}")
                notes.append({
                    "title": topic_title,
                    "content": topic_desc or f"Review your learning materials for {topic_title}.",
                    "key_points": [],
                })
        
        return notes


# Singleton instance
pdf_service = PDFService()
