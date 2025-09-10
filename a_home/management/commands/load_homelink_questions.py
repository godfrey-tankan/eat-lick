from django.core.management.base import BaseCommand
from a_home.models import JobSatisfactionQuestion

class Command(BaseCommand):
    help = 'Load Homelink survey questions into the database'
    
    def handle(self, *args, **options):
        # Section B: Job Satisfaction questions (1-30)
        section_b_questions = [
            ("I feel I am being paid a fair amount for the work I do.", "pay"),
            ("Salaries are frequently reviewed and are reasonable.", "pay"),
            ("I feel satisfied with my chances for salary increases.", "pay"),
            ("There is really lots of chances for promotion on my job.", "promotion"),
            ("Those who do well on the job stand a fair chance of being promoted.", "promotion"),
            ("I am satisfied with my chances for promotion.", "promotion"),
            ("My supervisor is very fair to me.", "supervision"),
            ("My supervisor shows a lot of interest in the feelings of subordinates.", "supervision"),
            ("I like my supervisor.", "supervision"),
            ("I am satisfied with the benefits I receive.", "fringe_benefits"),
            ("The benefits we receive are as good as most other organizations offer.", "fringe_benefits"),
            ("We receive all the benefits that we are supposed to be given.", "fringe_benefits"),
            ("When I do a good job, I receive the recognition for it that I should receive.", "contingent_rewards"),
            ("I feel that the work I do is appreciated.", "contingent_rewards"),
            ("Many of our rules and procedures make doing a good job easy.", "operating_conditions"),
            ("My efforts to do a good job are not blocked by red tape.", "operating_conditions"),
            ("I feel free to air my views without fear of victimisation.", "operating_conditions"),
            ("I enjoy working with my coworkers.", "coworkers"),
            ("I find my work a lot easier because I work with competent people.", "coworkers"),
            ("There is no much bickering and fighting at work.", "coworkers"),
            ("I feel that my job is very meaningful.", "nature_of_work"),
            ("I like doing the things I do at work.", "nature_of_work"),
            ("I feel a sense of pride in doing my job.", "nature_of_work"),
            ("Communications seem good within this organisation.", "communication"),
            ("The goals of this organisation are very clear for me.", "communication"),
            ("My work assignments are fully explained.", "communication"),
            ("My working environment is safe and secure.", "health_and_safety"),
            ("I have adequate protective clothing for my work.", "health_and_safety"),
            ("My job is less stressful.", "health_and_safety"),
            ("Programs promoting employee wellness are availed to me.", "health_and_safety"),
        ]

        # Section C: Job Engagement questions (31-39)
        section_c_questions = [
            ("At my work, I feel bursting with energy.", "vigour_energy"),
            ("At my job, I feel strong and vigorous.", "vigour_energy"),
            ("When I get up in the morning, I feel like going to work.", "vigour_energy"),
            ("I am enthusiastic about my job.", "dedication"),
            ("My job inspires me.", "dedication"),
            ("I am proud of the work that I do.", "dedication"),
            ("When I am working, I forget everything else around me.", "absorption"),
            ("I feel happy when I am working intensely.", "absorption"),
            ("I am immersed in my work.", "absorption"),
        ]

        # Combine all questions
        all_questions = section_b_questions + section_c_questions
        
        # First, delete all existing questions to ensure we only have the ones from the document
        JobSatisfactionQuestion.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Deleted all existing questions'))
        
        created_count = 0
        
        for i, (question_text, category) in enumerate(all_questions, 1):
            question = JobSatisfactionQuestion.objects.create(
                question_text=question_text,
                category=category,
                required=True
            )
            
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'Created question {i}: {question_text}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully loaded Homelink survey questions. Created: {created_count}, Total: {len(all_questions)}'
        ))