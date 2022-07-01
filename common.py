from appledirectory import AppleDirectory


def get_apple_dsid_from_email(email):

    ad = AppleDirectory()
    user = ad.get_user_by_email(email)
    apple_dsid = user.appleDSID.value

    return apple_dsid


def get_name_from_email(email):
    ad = AppleDirectory()
    user = ad.get_user_by_email(email)
    name = user.cn.value

    return name
