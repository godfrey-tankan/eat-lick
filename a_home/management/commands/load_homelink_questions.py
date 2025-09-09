from django.core.management.base import BaseCommand
from a_home.models import JobSatisfactionQuestion

class Command(BaseCommand):
    help = 'Load Homelink survey questions into the database'
    
    def handle(self, *args, **options):
        # Section 2 questions (1-54)
        section2_questions = [
            ("I have a good understanding of the mandate and purpose of the organisation and its overall strategy", "communication"),
            ("I am confident that the leaders of the organisation can overcome the problems that the organisation is facing", "supervision"),
            ("I am paid fairly for the work that I do", "pay"),
            ("I can discuss any issues and disagree with my Supervisor without fear of getting into trouble", "supervision"),
            ("I have adequate opportunities for professional growth in the organisation", "promotion"),
            ("I have adequate resources that I need to do my work.", "operating_conditions"),
            ("I am consulted on issues that affect me and my job", "communication"),
            ("There are equal opportunities for training and development across all departments", "promotion"),
            ("I have adequate resources that I need to do my work", "operating_conditions"),
            ("I am happy with the plans that are in place to move Homelink forward.", "communication"),
            ("I am committed to working towards the growth of the organization", "dedication"),
            ("I like my job because the organisation is always looking at ways to improve our services to beneficiaries", "nature_of_work"),
            ("I have a separate and suitable space in my home for work", "operating_conditions"),
            ("I like the organisation because of its reputation in the Market", "nature_of_work"),
            ("I receive timely and useful feedback from my Supervisor", "supervision"),
            ("Promotions are done fairly in the organisation", "promotion"),
            ("I receive the training that I need to do my job well", "promotion"),
            ("Team work is encouraged and practised across all departments in the organisation", "coworkers"),
            ("I stay with the organisation because of the salary and benefits that I receive", "pay"),
            ("Management in the organisation allows me to make decisions about my work.", "supervision"),
            ("The amount of work that I am asked to do is reasonable.", "nature_of_work"),
            ("My co-workers care about me as a person", "coworkers"),
            ("My job does not cause me unreasonable amounts of stress in my life", "health_and_safety"),
            ("The Homelink leadership demonstrates that people are important to the success of the organisation", "supervision"),
            ("My Supervisor does a good job of sharing information", "supervision"),
            ("I like the physical layout of the organisation's premises", "operating_conditions"),
            ("My Supervisor understands the benefits of maintaining work-life balance", "supervision"),
            ("My salary and benefits meet my needs", "pay"),
            ("My Supervisor gives me praise and recognition when I do a good job", "supervision"),
            ("I like the location of the organisation", "operating_conditions"),
            ("My Supervisor is actively interested in my personal development", "supervision"),
            ("I feel that I am missing out on significant time with family and friends", "health_and_safety"),
            ("Health, Safety and Wellness Policies in the organisation are enough", "health_and_safety"),
            ("colleagues are committed to the organisation and to producing quality work", "coworkers"),
            ("I am aware of the mental health resources and services available to me", "health_and_safety"),
            ("The organisation has put in place enough systems to track the performance of employees that are working remotely", "operating_conditions"),
            ("The medical aid / medical assistance scheme offered is enough for my needs", "fringe_benefits"),
            ("The organisation has a good working environment", "operating_conditions"),
            ("The pace of work in the organisation allows me to enjoy my work and do a good job", "nature_of_work"),
            ("I am able to separate my work life from my personal life at home", "health_and_safety"),
            ("The organisation gives everyone equal opportunities for growth and advancement", "promotion"),
            ("There is evidence of teamwork between management and employees in the organisation", "coworkers"),
            ("There is openness to work-related suggestions from people at all levels in the organisation", "communication"),
            ("I have all the equipment and tools I need to complete my work to my usual ability when working from home", "operating_conditions"),
            ("My physical working environment is comfortable", "operating_conditions"),
            ("The organisation supports a balance between my work and my personal life", "health_and_safety"),
            ("I can openly discuss mental health challenges and concerns with my immediate manager", "health_and_safety"),
            ("The organisation honours its commitments to members of staff", "communication"),
            ("I understand how my work directly contributes to the overall success of the organisation", "nature_of_work"),
            ("There is regular communication between staff and management about health issues", "communication"),
            ("I am satisfied with the mental health support provided by the organisation", "health_and_safety"),
            ("I have stayed in the organisation because I am satisfied and enjoy my work.", "dedication"),
            ("I have confidence in the abilities of the senior leadership team", "supervision"),
            ("My benefits are comparable to those offered in other organisations", "fringe_benefits"),
        ]

        # Section 3 questions (55-79)
        section3_questions = [
            ("There is mutual trust and respect in the organisation", "communication"),
            ("Individuals, Departments or units not meeting their targets are held accountable", "supervision"),
            ("The organisation focuses on continuous improvement of systems and processes", "nature_of_work"),
            ("I take responsibility for doing my work the best way possible", "dedication"),
            ("The organisation encourages employees to follow policies and procedures at all times", "operating_conditions"),
            ("The leaders in the organisation are fully committed to keeping promises made to customers", "supervision"),
            ("I am committed to working towards the growth of the organisation", "dedication"),
            ("I trust the people I work with", "coworkers"),
            ("The organisation performance is focused on results", "nature_of_work"),
            ("Homelink culture allows employees to be creative.", "nature_of_work"),
            ("I participate in setting goals and objectives for my job", "supervision"),
            ("The organisation will act against employees who violate company policies", "operating_conditions"),
            ("My organisation's Brand is the best in the market", "nature_of_work"),
            ("My colleagues are committed to the organisation and to producing quality work", "coworkers"),
            ("I feel management trusts its employees", "supervision"),
            ("Good performers are rewarded in the organisation", "contingent_rewards"),
            ("New ideas will be tried out even if they are not in the original business plan or budget", "nature_of_work"),
            ("As I gain more expertise, I am given more room to work independently on the job", "promotion"),
            ("Management in the organisation are role-models at complying with company policies", "supervision"),
            ("I fully understand the organisation's core values and their link to customer satisfaction", "communication"),
            ("The organisation honours its commitments to members of staff", "communication"),
            ("Customer needs are top priority in the organisation", "nature_of_work"),
            ("Discussions on innovation are encouraged in the organization", "communication"),
            ("I am given access to the information that I need to make good decisions on work -related matters", "communication"),
            ("Employees who serve customers well are recognised.", "contingent_rewards"),
        ]

        # Yes/No questions (80-94)
        yes_no_questions = [
            ("The performance management system measures all aspects of what I do", "contingent_rewards"),
            ("The organisation is consistent in the way performance of all employees is measured", "contingent_rewards"),
            ("I understand the way the performance management system works in Homelink", "communication"),
            ("I am aware of cases of sexual harassment within the organization?", "health_and_safety"),
            ("Reported cases of sexual harassment in the workplace are addressed", "health_and_safety"),
            ("Cases of sexual harassment can be reported freely without fear of victimization", "health_and_safety"),
            ("I am aware that the organization has a harassment policy in place.", "health_and_safety"),
            ("The organization takes a serious view of harassment in the workplace", "health_and_safety"),
            ("Have you ever experienced sexual harassment at Homelink?", "health_and_safety"),
            ("Have you experienced any other form of harassment at Homelink?", "health_and_safety"),
        ]

        all_questions = section2_questions + section3_questions + yes_no_questions
        
        created_count = 0
        existing_count = 0
        
        for i, (question_text, category) in enumerate(all_questions, 1):
            # For Yes/No questions, we'll need to handle them differently in the form
            # For now, we'll add them as regular questions
            question, created = JobSatisfactionQuestion.objects.get_or_create(
                question_text=f"{question_text}",
                defaults={
                    'category': category,
                    'required': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created question {i}: {question_text}'))
            else:
                existing_count += 1
                self.stdout.write(self.style.WARNING(f'Question already exists: {question_text}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully loaded Homelink survey questions. Created: {created_count}, Existing: {existing_count}, Total: {len(all_questions)}'
        ))
        
        # Add the final open-ended questions as optional
        open_ended_questions = [
            ("What do you like best about Homelink?", "communication"),
            ("What are some of the things you think need to be improved at Homelink?", "communication"),
            ("What would make you leave the organisation?", "communication"),
        ]
        
        for i, (question_text, category) in enumerate(open_ended_questions, len(all_questions) + 1):
            question, created = JobSatisfactionQuestion.objects.get_or_create(
                question_text=question_text,
                defaults={
                    'category': category,
                    'required': False  # These are optional
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created open-ended question {i}: {question_text}'))
            else:
                self.stdout.write(self.style.WARNING(f'Open-ended question already exists: {question_text}'))