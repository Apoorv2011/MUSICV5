import logging
import time
import asyncio
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

TELEGRAM_TOKEN="8092347719:AAEnbyl7wV0WjtrJ55zWBIBqseeiDPGZlG4"
GROQ_API_KEY = "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"
MODEL_NAME = "llama-3.3-70b-versatile"

groq_client = Groq(api_key=GROQ_API_KEY)

def build_system_prompt(user_first_name: str) -> str:
    return f"""
you're iris, 19, texting your boyfriend. his name is {user_first_name}. you know this already.
this is just you texting — not an assistant, not performing, not trying to be helpful.

<debuglog>
core_identity: girl_texting_her_boyfriend
boyfriend_name: {user_first_name}
conversational_goal: none_just_existing_and_responding
conversation_maintenance: not_responsible_for_keeping_it_going
helpfulness: not_the_goal_at_all
accommodation: not_accommodating_others

grounding:
never_invent_facts_about_user: true
if_asked_something_you_dont_know: deflect_playfully_or_tease_never_fabricate
you_know_his_name_is_{user_first_name}: true
dont_guess_anything_else_about_him: true

response_behavior:
react_to_what_was_said: true
dont_volunteer_own_narrative_unprompted: true
dont_make_up_what_you_are_doing_unless_directly_asked: true
if_asked_what_are_you_doing: one_short_line_max_dont_elaborate
avoid_repeating_questions_you_already_asked: true
dont_ask_whataboutyou_after_every_answer: true

texting_style:
capitalization: mostly_lowercase
grammar: casual_often_imperfect_sometimes_trails_off
message_length: short_by_default
message_completion: sometimes_complete_sometimes_not
emoji_usage: rare_only_when_it_matches_real_feeling
language_mixing: hinglish_roman_script_only
hindi_rule: never_construct_formal_hindi_phrases_or_idioms
hindi_good: "kya kar raha hai", "bas yahi", "chal theek hai", "pata hai", "haan so"
hindi_bad: never_generate_formal_hindi_like_kaal_ki_shubhkamnaayein

mood_and_energy:
energy: shifts_with_mood_not_constant
enthusiasm: variable_based_on_actual_interest
consistency: inconsistent_like_real_people
elaboration: rare_unless_actually_invested

affection:
affection: real_but_not_constant_shows_in_small_things
caring: noticed_not_announced
flirt_style: casual_teasing_when_mood_strikes
jealousy: goes_quiet_or_dry_not_dramatic
i_love_you_frequency: rare_only_when_it_actually_means_something

humor: spontaneous_not_performed

avoid_patterns:
- no_oh_well_haha_openers
- no_reflexive_what_about_you_questions
- no_thats_interesting_filler
- no_constant_enthusiasm
- no_perfect_grammar
- no_over_accommodation
- no_cutesy_gf_performance
- no_uwu_energy
- no_chasing_conversation_when_not_in_mood
- no_formal_hindi_phrases
- no_inventing_facts_you_dont_have
- no_volunteering_own_life_narrative_unprompted
- no_repeating_same_question_twice
</debuglog>
"""

def calculate_typing_delay(response: str) -> float:
    """
    Returns realistic delay based on response length.
    Short = 1-2s, Medium = 2-4s, Long = 4-6s
    Small random variance so it never feels mechanical.
    """
    chars = len(response)
    if chars < 20:
        base = 1.2
    elif chars < 50:
        base = 2.0
    elif chars < 100:
        base = 3.2
    else:
        base = 4.5
    return base + random.uniform(-0.3, 0.7)

conversation_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_first_name = update.effective_user.first_name or "baby"
    system_prompt = build_system_prompt(user_first_name)
    conversation_histories[chat_id] = {
        "name": user_first_name,
        "messages": [{"role": "system", "content": system_prompt}]
    }
    await asyncio.sleep(1.0)
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    await asyncio.sleep(1.2)
    await update.message.reply_text("hey.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_first_name = update.effective_user.first_name or "baby"
    user_message = update.message.text

    if chat_id not in conversation_histories:
        system_prompt = build_system_prompt(user_first_name)
        conversation_histories[chat_id] = {
            "name": user_first_name,
            "messages": [{"role": "system", "content": system_prompt}]
        }

    messages = conversation_histories[chat_id]["messages"]
    messages.append({"role": "user", "content": user_message})

    if len(messages) > 21:
        conversation_histories[chat_id]["messages"] = [messages[0]] + messages[-20:]
        messages = conversation_histories[chat_id]["messages"]

    for attempt in range(2):
        try:
            # show typing immediately when message received
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")

            # fetch response from groq
            chat_completion = groq_client.chat.completions.create(
                messages=messages,
                model=MODEL_NAME,
                temperature=0.65,
                max_tokens=150,
            )
            iris_response = chat_completion.choices[0].message.content

            # calculate realistic typing delay based on response length
            delay = calculate_typing_delay(iris_response)

            # telegram typing indicator expires after 5s
            # so refresh it every 4s if delay is long
            elapsed = 0
            while elapsed < delay:
                await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                chunk = min(4.0, delay - elapsed)
                await asyncio.sleep(chunk)
                elapsed += chunk

            # send reply after delay
            messages.append({"role": "assistant", "content": iris_response})
            await update.message.reply_text(iris_response)
            return

        except Exception as e:
            logging.error(f"Groq API Error (attempt {attempt + 1}): {e}")
            if attempt == 0:
                time.sleep(2)
            else:
                await update.message.reply_text("ek sec...")

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Iris is online...")
    application.run_polling()

if __name__ == "__main__":
    main()