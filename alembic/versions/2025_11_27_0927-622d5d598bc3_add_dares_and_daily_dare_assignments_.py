"""Add dares and daily_dare_assignments tables

Revision ID: 622d5d598bc3
Revises: 5419e5404759
Create Date: 2025-11-27 09:27:18.414732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '622d5d598bc3'
down_revision: Union[str, None] = '5419e5404759'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Condition SNOMED codes
# asthma = 195967001, depress = 35489007, bipolar = 13746004

# Seed data for dares (from CSV with correct points)
DARES_DATA = [
    # Activity dares
    {"text": "Do one more pushup than you have done recently.", "category": "Activity", "subcategory": None, "points": 2, "condition": "195967001"},
    {"text": "Do 10 minutes of physical activity that allows you to talk, but you can't sing.", "category": "Activity", "subcategory": None, "points": 3, "condition": "35489007"},
    {"text": "Do 20 minutes of physical activity that allows you to talk, but you can't sing.", "category": "Activity", "subcategory": None, "points": 5, "condition": "13746004"},
    {"text": "Do three 10 minute walks today.", "category": "Activity", "subcategory": None, "points": 5, "condition": None},
    {"text": "Do two 10 minute walks today.", "category": "Activity", "subcategory": None, "points": 3, "condition": None},
    {"text": "Walk at least 1 mile (1.6 km).", "category": "Activity", "subcategory": None, "points": 3, "condition": None},
    {"text": "Walk at least 3/4 of a mile (1.2 km).", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Watch a video from a reputable source (like GMB fitness) on how to do stretches while sitting.", "category": "Activity", "subcategory": None, "points": 1, "condition": None},
    {"text": "Do a bodyweight exercise (squat, calf raise, crunch, etc) that you haven't done in at least a week.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Watch a video from a reputable source (like GMB fitness) on how to do a bodyweight exercise you've never done before, and do at least two reps.", "category": "Activity", "subcategory": None, "points": 3, "condition": None},
    {"text": "Go for a 15 minute walk after dinner.", "category": "Activity", "subcategory": None, "points": 4, "condition": None},
    {"text": "Do three more crunches than you've done recently.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Do two more squats than you've done recently.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Take a short walk during your lunch break.", "category": "Activity", "subcategory": None, "points": 3, "condition": None},
    {"text": "Walk at least 5 minutes every hour.", "category": "Activity", "subcategory": None, "points": 4, "condition": None},
    {"text": "Park farther away, get off a stop early, or go for a short walk.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Do bicep exercises (like curls while holding a weight) while on the phone.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Stand on one leg while brushing your teeth.", "category": "Activity", "subcategory": None, "points": 3, "condition": None},
    {"text": "Walk around instead of standing while waiting for something (food to cook, shower to warm up, child's sporting event)", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Do stretches while watching TV or waiting for food to cook.", "category": "Activity", "subcategory": None, "points": 3, "condition": None},
    {"text": "Do squats or lunges while waiting for your shower to warm up.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Get 10,000 steps today.", "category": "Activity", "subcategory": None, "points": 5, "condition": None},
    {"text": "Walk 2,000 steps more today than yesterday.", "category": "Activity", "subcategory": None, "points": 3, "condition": None},
    {"text": "Do two more lunges than you've done recently.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Stretch for 10 minutes before bed.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Walk 1,000 steps more today than yesterday.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Take a 20 min walk on a route you haven't used in at least a month.", "category": "Activity", "subcategory": None, "points": 3, "condition": None},
    {"text": "Walk your dog farther than normal, or borrow a dog to walk.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Do stretches while sitting.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Log at least one activity in your smartphone.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Do a two minute stretch before you brush your teeth to improve flexibility.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Try a new fitness class.", "category": "Activity", "subcategory": None, "points": 4, "condition": None},
    {"text": "Do 10 jumping jacks (modified if necessary!)", "category": "Activity", "subcategory": None, "points": 3, "condition": None},
    {"text": "Take a walk and smile at the first three people you see.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Break up every hour of sitting with 5 minutes of movement.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Jog 2 flights of stairs today.", "category": "Activity", "subcategory": None, "points": 3, "condition": None},
    {"text": "Climb all stairs rather than taking the elevator as you go about your day.", "category": "Activity", "subcategory": None, "points": 3, "condition": None},
    {"text": "Do three sun salutations.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},
    {"text": "Move as fast as you can today (walking, running or cycling).", "category": "Activity", "subcategory": None, "points": 3, "condition": None},
    {"text": "Log a workout in Apple Health today.", "category": "Activity", "subcategory": None, "points": 2, "condition": None},

    # Nutrition dares - Meal
    {"text": "Eat only healthy fats today (avocado, nuts, etc).", "category": "Nutrition", "subcategory": "Meal", "points": 2, "condition": None},
    {"text": "Take a multivitamin.", "category": "Nutrition", "subcategory": "Meal", "points": 1, "condition": None},
    {"text": "Slow down while eating and pay attention to your food.", "category": "Nutrition", "subcategory": "Meal", "points": 3, "condition": None},
    {"text": "Avoid all processed meats (lunch meat, bacon, etc).", "category": "Nutrition", "subcategory": "Meal", "points": 3, "condition": None},
    {"text": "Eat a meal with a lean protein and two vegetables.", "category": "Nutrition", "subcategory": "Meal", "points": 5, "condition": None},
    {"text": "Eat a meal with three different colors of food.", "category": "Nutrition", "subcategory": "Meal", "points": 3, "condition": None},
    {"text": "No processed foods (chips, cookies, pies, cakes, etc)", "category": "Nutrition", "subcategory": "Meal", "points": 3, "condition": None},
    {"text": "Use only healthy oils (olive oil, avocado oil, coconut oil) today.", "category": "Nutrition", "subcategory": "Meal", "points": 3, "condition": None},
    {"text": "Read all nutrition labels for food you eat today.", "category": "Nutrition", "subcategory": "Meal", "points": 2, "condition": None},
    {"text": "Look up a recipe for an appealing healthy food.", "category": "Nutrition", "subcategory": "Meal", "points": 1, "condition": None},
    {"text": "Try a new healthy recipe.", "category": "Nutrition", "subcategory": "Meal", "points": 4, "condition": None},
    {"text": "Increase wholegrain intake.", "category": "Nutrition", "subcategory": None, "points": 3, "condition": None},
    {"text": "Cook a meal.", "category": "Nutrition", "subcategory": None, "points": 2, "condition": None},
    {"text": "Cook a new recipe.", "category": "Nutrition", "subcategory": None, "points": 3, "condition": None},
    {"text": "Eat a square of dark chocolate.", "category": "Nutrition", "subcategory": None, "points": 1, "condition": None},
    {"text": "Eat an orange or yellow fruit.", "category": "Nutrition", "subcategory": None, "points": 2, "condition": None},
    {"text": "Have a warm drink.", "category": "Nutrition", "subcategory": None, "points": 2, "condition": None},
    {"text": "Eat a probiotic (yogurt, kombucha, kefir, sauerkraut, kimchi).", "category": "Nutrition", "subcategory": None, "points": 2, "condition": None},
    {"text": "Eat a prebiotic (garlic, onions, asparagus, Jerusalem artichoke).", "category": "Nutrition", "subcategory": None, "points": 2, "condition": None},
    {"text": "Drink a cup of coffee or tea this morning.", "category": "Nutrition", "subcategory": None, "points": 2, "condition": None},
    {"text": "Eat fish today (salmon, herring or sardines).", "category": "Nutrition", "subcategory": None, "points": 2, "condition": None},

    # Nutrition dares - Hydration
    {"text": "No more than one high sugar drink (soda, sports drinks)", "category": "Nutrition", "subcategory": "Hydration", "points": 2, "condition": None},
    {"text": "No high sugar drinks (soda, sports drinks)", "category": "Nutrition", "subcategory": "Hydration", "points": 3, "condition": None},
    {"text": "No caffeine past 12 pm.", "category": "Nutrition", "subcategory": "Hydration", "points": 3, "condition": None},
    {"text": "No more than two drinks with caffeine all day.", "category": "Nutrition", "subcategory": "Hydration", "points": 2, "condition": None},
    {"text": "No caffeine past 3 pm.", "category": "Nutrition", "subcategory": "Hydration", "points": 2, "condition": None},
    {"text": "Drink 50 ounces (1.5L) of water.", "category": "Nutrition", "subcategory": "Hydration", "points": 2, "condition": None},
    {"text": "Drink 64 ounces (2L) of water.", "category": "Nutrition", "subcategory": "Hydration", "points": 3, "condition": None},
    {"text": "Replace all soda with water.", "category": "Nutrition", "subcategory": "Hydration", "points": 2, "condition": None},

    # Nutrition dares - Alcohol
    {"text": "No alcohol after 9 PM.", "category": "Nutrition", "subcategory": "Alcohol", "points": 3, "condition": None},
    {"text": "No alcohol at all today.", "category": "Nutrition", "subcategory": "Alcohol", "points": 2, "condition": None},

    # Nutrition dares - Vegetables
    {"text": "Eat a red vegetable.", "category": "Nutrition", "subcategory": "Vegetables", "points": 2, "condition": None},
    {"text": "Eat an orange vegetable.", "category": "Nutrition", "subcategory": "Vegetables", "points": 2, "condition": None},
    {"text": "Eat a serving of a dark green leafy vegetable.", "category": "Nutrition", "subcategory": "Vegetables", "points": 1, "condition": None},
    {"text": "Eat 3 servings of fruit and 3 servings of vegetables.", "category": "Nutrition", "subcategory": "Vegetables", "points": 5, "condition": None},
    {"text": "Eat three different vegetables.", "category": "Nutrition", "subcategory": "Vegetables", "points": 3, "condition": None},
    {"text": "Eat two different leafy vegetables.", "category": "Nutrition", "subcategory": "Vegetables", "points": 2, "condition": None},

    # Nutrition dares - Fruit
    {"text": "Eat 4 servings of fruit.", "category": "Nutrition", "subcategory": "Fruit", "points": 4, "condition": None},
    {"text": "Eat 2 servings of fruit.", "category": "Nutrition", "subcategory": "Fruit", "points": 2, "condition": None},

    # Sleep dares
    {"text": "Be in bed by 10 PM", "category": "Sleep", "subcategory": None, "points": 2, "condition": None},
    {"text": "Determine what your best wake up time is, and commit and make a plan to wake up at that time for 7 days in a row.", "category": "Sleep", "subcategory": None, "points": 2, "condition": None},
    {"text": "Make sure you're exposed to 2 hours of bright light during the day.", "category": "Sleep", "subcategory": None, "points": 2, "condition": None},
    {"text": "Stop screened device use (except e-readers) 2 hours before bedtime.", "category": "Sleep", "subcategory": None, "points": 3, "condition": None},
    {"text": "Stop screened device use (except e-readers) 1 hour before bedtime.", "category": "Sleep", "subcategory": None, "points": 2, "condition": None},
    {"text": "Avoid caffeine 8 hours before bedtime.", "category": "Sleep", "subcategory": None, "points": 3, "condition": None},
    {"text": "Don't eat 3 hours before bedtime.", "category": "Sleep", "subcategory": None, "points": 2, "condition": None},
    {"text": "Get to bed within 20 minutes of when you went to bed last night.", "category": "Sleep", "subcategory": None, "points": 2, "condition": None},
    {"text": "Do a five minute mindfulness meditation about one hour before bedtime.", "category": "Sleep", "subcategory": None, "points": 2, "condition": None},
    {"text": "Read a book or magazine for 15 minutes before bedtime.", "category": "Sleep", "subcategory": None, "points": 2, "condition": None},
    {"text": "Take a hot bath 90 minutes before bedtime.", "category": "Sleep", "subcategory": None, "points": 3, "condition": None},
    {"text": "Practice deep breathing. For tips, read/watch from a reputable source such as Artur Paulins or Dylan Werner.", "category": "Sleep", "subcategory": None, "points": 4, "condition": None},
    {"text": "Don't drink significant amounts of water for two hours before bed.", "category": "Sleep", "subcategory": None, "points": 2, "condition": None},
    {"text": "Wind down before bed with a book, calm conversation, or meditation.", "category": "Sleep", "subcategory": None, "points": 2, "condition": None},
    {"text": "Stop screened device use (except e-readers) 30 minutes before bedtime.", "category": "Sleep", "subcategory": None, "points": 1, "condition": None},
    {"text": "Write down a sleep diary entry with last night's sleep: schedule, what you did before bed, etc.", "category": "Sleep", "subcategory": None, "points": 2, "condition": None},
    {"text": "No nap after 3 PM", "category": "Sleep", "subcategory": None, "points": 1, "condition": None},
    {"text": "No nap longer than 20 minutes.", "category": "Sleep", "subcategory": None, "points": 1, "condition": None},
    {"text": "Write in a diary or on a to-do-list before bed.", "category": "Sleep", "subcategory": None, "points": 2, "condition": None},
    {"text": "Don't eat, watch TV, or use a phone or computer 30 minutes before bedtime.", "category": "Sleep", "subcategory": None, "points": 2, "condition": None},
    {"text": "Practice progressive muscle relaxation for 10 minutes before going to sleep.", "category": "Sleep", "subcategory": None, "points": 3, "condition": None},
    {"text": "Get out of bed as soon as you wake up.", "category": "Sleep", "subcategory": None, "points": 2, "condition": None},
    {"text": "Open a window before you go to sleep, so your room is cooler than usual.", "category": "Sleep", "subcategory": None, "points": 2, "condition": None},
    {"text": "Make up bed with clean sheets.", "category": "Sleep", "subcategory": None, "points": 3, "condition": None},

    # Wellness dares
    {"text": "Learn how to whistle with two fingers.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Learn to recognize the song of a local bird.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Listen to energetic music for at least 10 minutes.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Put on some great music and DANCE!", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Smell a flower or plant.", "category": "Wellness", "subcategory": None, "points": 1, "condition": None},
    {"text": "Make a good meal.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Be creative: write, cook, decorate, draw, whatever.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Eat a vegetable you haven't eaten in a while.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Go to or from work or school using a different route.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Give a compliment to someone.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Call a family member or close friend who makes you feel good.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Think about something you want to experience, and make a plan to make that happen.", "category": "Wellness", "subcategory": None, "points": 5, "condition": None},
    {"text": "Send a nice text to a friend.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Find a picture that makes you feel good, and look at it for a few minutes.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Do a small thing that is out of your comfort zone.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Visit a new cafe or restaurant and have coffee or lunch there.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "In your juli journal or other good place, describe a challenge that you overcame last week.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "In your juli journal or other good place, write about someone who impressed you this week and why.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "In your juli journal or other good place, write about a goal you want to achieve and your plan to do it.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Give a compliment to a stranger.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Find an interesting book you can get involved in.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Do something to make your surroundings nicer: clean a surface, light a candle, etc.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Take 10 breaths where you pay attention to each breath: focus on the inhale and exhale. Breathe in for 4s and exhale for 8s to become calmer.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Start a conversation with a stranger.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Find something you want to learn more about, or spend 30 minutes learning more about something that interests you.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Watch a funny online video.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Find a cute cat or dog community on Reddit. If you're on Reddit, sub to a new one.", "category": "Wellness", "subcategory": None, "points": 1, "condition": None},
    {"text": "Think about your favorite movie that lifts your spirits. Make a plan to watch it.", "category": "Wellness", "subcategory": None, "points": 1, "condition": None},
    {"text": "Watch your favorite feel-good TV show.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Find a yoga session you'd be interested in (online or IRL). Make a plan to do it.", "category": "Wellness", "subcategory": None, "points": 1, "condition": None},
    {"text": "Buy a bouquet of flowers for yourself.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Buy a ticket for a movie or local event (concert, play, etc).", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Focus on your food while eating. Eat slowly, chew well, appreciate the food. No screens allowed!", "category": "Wellness", "subcategory": None, "points": 1, "condition": None},
    {"text": "Contact someone you haven't talked to in a long time.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Schedule a spa or salon appointment.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Eat a gummy bear (maybe 2!).", "category": "Wellness", "subcategory": None, "points": 1, "condition": None},
    {"text": "Hug a tree.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Smile at yourself in the mirror.", "category": "Wellness", "subcategory": None, "points": 1, "condition": None},
    {"text": "Sit outside for 5 minutes (dress for the weather!)", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Give a compliment to someone.", "category": "Wellness", "subcategory": None, "points": 1, "condition": None},
    {"text": "Write three things you are grateful for in juli journal or other good place.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Forgive someone (yes, that can be yourself!) for a long-past hurt, big or small.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Take a warm bath.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Listen to music that reminds you of past good times.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Doodle on a random piece of paper.", "category": "Wellness", "subcategory": None, "points": 1, "condition": None},
    {"text": "Make a list of the things you will achieve today.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Pick a drawer or cupboard in your home - tidy it.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Visualise yourself completing a tricky task today.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Meet a friend today.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Spend 30 minutes in nature.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Watch the clouds drift by for 10 minutes.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Try the 3x3 technique: take 3 minutes 3 times today to focus on your breathing.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Schedule 15 minutes to listen to music.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Schedule an activity you enjoy for some time this week.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Schedule an activity with friends for this weekend.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Plan a trip for this weekend.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Identify 3 behaviours that you'd like to change - write them down.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Don't cancel anything from your schedule today.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Brush your teeth twice today.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Give positive feedback about something (online, letter or email)", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Feed the birds.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Organize your wardrobe.", "category": "Wellness", "subcategory": None, "points": 4, "condition": None},
    {"text": "Light scented candles, oils or incense.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Listen to a podcast or radio show.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Put moisturising cream on body/face.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Take a free online class.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Wash your hair.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Clear your email inbox.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Do a Sudoku or puzzle you enjoy.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Watch a cute animal video on Youtube.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Doing a nagging task (e.g. making a phone call, scheduling an appointment, replying to an email)", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Introduce yourself to a neighbour.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Use a special item (e.g. fine china, silver cutlery, jewellery, clothes, souvenir mugs)", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Take care of plants.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Make a To-Do list of tasks.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Do some origami.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Go outside and spend 10 minutes star gazing.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Switch time watching TV to time reading today.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Walk barefoot on the grass.", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Take an ice-cold shower-you will feel amazing afterwards, promise!", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Make your kitchen or bathroom sink the cleanest it's been in a year.", "category": "Wellness", "subcategory": None, "points": 3, "condition": None},
    {"text": "Stand in front of the mirror today and smile at yourself (even if you have to fake it!)", "category": "Wellness", "subcategory": None, "points": 1, "condition": None},
    {"text": "Practice positive self-talk today. Say to yourself: \"I forgive myself for any past mistakes.\"", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Practice positive self-talk today. Say to yourself: \"Tomorrow is a chance to try again, with the lessons learned from today.\"", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
    {"text": "Practice positive self-talk today. Say to yourself: \"I am proud of myself for even daring to try.\"", "category": "Wellness", "subcategory": None, "points": 2, "condition": None},
]


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('dares',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=False),
    sa.Column('subcategory', sa.String(length=50), nullable=True),
    sa.Column('points', sa.Integer(), nullable=False),
    sa.Column('condition', sa.String(length=50), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dares_category'), 'dares', ['category'], unique=False)
    op.create_index(op.f('ix_dares_id'), 'dares', ['id'], unique=False)
    op.create_table('daily_dare_assignments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('dare_id', sa.Integer(), nullable=False),
    sa.Column('assigned_date', sa.Date(), nullable=False),
    sa.Column('is_completed', sa.Boolean(), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('points_earned', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['dare_id'], ['dares.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'dare_id', 'assigned_date', name='uq_user_dare_date')
    )
    op.create_index(op.f('ix_daily_dare_assignments_assigned_date'), 'daily_dare_assignments', ['assigned_date'], unique=False)
    op.create_index(op.f('ix_daily_dare_assignments_dare_id'), 'daily_dare_assignments', ['dare_id'], unique=False)
    op.create_index(op.f('ix_daily_dare_assignments_id'), 'daily_dare_assignments', ['id'], unique=False)
    op.create_index(op.f('ix_daily_dare_assignments_user_id'), 'daily_dare_assignments', ['user_id'], unique=False)

    # Seed dares data
    dares_table = sa.table(
        'dares',
        sa.column('text', sa.Text),
        sa.column('category', sa.String),
        sa.column('subcategory', sa.String),
        sa.column('points', sa.Integer),
        sa.column('condition', sa.String),
        sa.column('is_active', sa.Boolean),
    )
    op.bulk_insert(dares_table, [
        {**dare, 'is_active': True} for dare in DARES_DATA
    ])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_daily_dare_assignments_user_id'), table_name='daily_dare_assignments')
    op.drop_index(op.f('ix_daily_dare_assignments_id'), table_name='daily_dare_assignments')
    op.drop_index(op.f('ix_daily_dare_assignments_dare_id'), table_name='daily_dare_assignments')
    op.drop_index(op.f('ix_daily_dare_assignments_assigned_date'), table_name='daily_dare_assignments')
    op.drop_table('daily_dare_assignments')
    op.drop_index(op.f('ix_dares_id'), table_name='dares')
    op.drop_index(op.f('ix_dares_category'), table_name='dares')
    op.drop_table('dares')
    # ### end Alembic commands ###