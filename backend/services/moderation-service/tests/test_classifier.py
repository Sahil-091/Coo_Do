from app.classifier import classify_non_safety


def test_classifies_each_non_safety_category_before_publication():
    assert classify_non_safety("You are a worthless idiot") == ["toxicity_or_harassment"]
    assert classify_non_safety("Please send nudes") == ["sexual_content"]
    assert classify_non_safety("Guaranteed returns: send money today") == ["spam_or_scam"]


def test_clean_supportive_post_is_not_held_by_non_safety_classifier():
    assert classify_non_safety("I am anxious about tomorrow's exam and could use some encouragement.") == []


def test_holds_contact_details_and_off_platform_or_dating_approaches():
    assert classify_non_safety("My number is +91 98765 43210") == ["personal_contact_or_location"]
    assert classify_non_safety("DM me and move to WhatsApp") == ["off_platform_or_dating_approach"]


def test_holds_address_like_meetup_copy_for_human_review():
    assert classify_non_safety("Meet at 12 Baker Street") == ["personal_contact_or_location"]
