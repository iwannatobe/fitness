# compatibility re-export
from models.database import get_db, init_db
from models.strength_model import add_strength, get_last_strength, get_strength_records, delete_strength
from models.cardio_model import add_cardio, get_last_cardio, get_cardio_records, delete_cardio
from models.body_model import add_body, get_body_records, delete_body
from models.plan_model import clear_today_plan, add_plan_item, get_today_plan, complete_plan_item, delete_plan_item, update_plan_item
from models.training_session_model import (
    cancel_rest_timer, finish_today_training_session_if_complete,
    get_today_training_session, mark_rest_timer_notified, start_rest_timer,
    start_today_training_session,
)
from models.catalog_model import (
    find_catalog_exercise, get_catalog_exercise, resolve_media_path, search_catalog,
)
from models.template_model import add_template, get_templates, delete_template, update_template
from models.metrics_model import get_user_weight, set_user_weight, calc_strength_calories, calc_cardio_calories
from models.nuke_model import add_nuke_marker, is_date_nuked, get_nuke_dates
from models.calendar_model import (
    get_active_dates, get_date_detail, get_date_overview, get_date_template_name,
)
from models.exercise_model import get_custom_exercises, add_custom_exercise, delete_custom_exercise
from models.profile_model import get_profile, set_profile
from models.meal_model import add_meal, get_today_meals, get_meals_for_date, delete_meal
from models.calorie_model import (
    get_bmr, get_tdee, today_intake, today_exercise_burn,
    today_balance, weight_trend, today_summary_text,
)
