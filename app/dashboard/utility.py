##### UTILITY ###############
days_of_the_week = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
def copy_message_data(source, target_model):
    copy = target_model(
        id=source.id,
        user=source.user,
        title=source.title,
        content=source.content,
        timestamp=source.timestamp,
        task=source.task,
        picture=source.picture,
        content_type=source.content_type
    )
    copy.save()
    copy.recipient.set(source.recipient.all())
    return copy



def safe_divide(numerator, denominator):
            try:
                return (numerator / denominator) * 100
            except ZeroDivisionError:
                return 0
    