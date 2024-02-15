# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class Files(models.Model):
    filename = models.CharField(max_length=120)
    filename_unzipped = models.CharField(max_length=120)
    format = models.CharField(max_length=6)
    insttext = models.TextField()
    genre_id = models.IntegerField()
    hash = models.CharField(unique=True, max_length=33)
    download = models.TextField()
    hits = models.IntegerField()
    timestamp = models.DateTimeField()
    date = models.DateTimeField()
    filterer = models.CharField(max_length=60)
    songtitle = models.TextField()
    comment = models.TextField()
    filesize = models.BigIntegerField()
    channels = models.PositiveIntegerField()
    comment_score = models.DecimalField(max_digits=10, decimal_places=1)
    comment_total = models.IntegerField()
    review_score = models.DecimalField(max_digits=10, decimal_places=0)
    review_total = models.IntegerField()
    license = models.TextField()
    hide_text = models.CharField(max_length=1)
    patternhash = models.CharField(max_length=16, blank=True, null=True)
    artist_file = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'files'


class FilesNew(models.Model):
    filename = models.CharField(max_length=120)
    filename_unzipped = models.CharField(max_length=120)
    hash = models.CharField(unique=True, max_length=33)
    uploader = models.CharField(max_length=14)
    insttext = models.TextField()
    uploader_uid = models.IntegerField()
    attach_to_ids = models.TextField()
    dateuploaded = models.DateTimeField()
    songtitle = models.TextField()
    comment = models.TextField()
    filesize = models.BigIntegerField()
    channels = models.PositiveIntegerField()
    ismine = models.CharField(max_length=1)
    flag = models.CharField(max_length=10)
    flagged_by = models.IntegerField()
    patternhash = models.CharField(max_length=16, blank=True, null=True)
    artist_file = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'files_new'


class Genres(models.Model):
    genre_id = models.AutoField(primary_key=True)
    total = models.IntegerField()
    genre = models.TextField()
    child_of = models.IntegerField()
    parent = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'genres'


class TmaActionMessages(models.Model):
    type = models.TextField()
    userid = models.IntegerField()
    actiontext = models.TextField()
    moduleid = models.IntegerField()
    date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'tma_action_messages'


class TmaArtistMappingsPsuedo(models.Model):
    artist = models.TextField()
    hash = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_artist_mappings_psuedo'


class TmaArtistMappingsReal(models.Model):
    artist = models.TextField()
    hash = models.TextField()
    filename = models.TextField()
    description = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_artist_mappings_real'


class TmaArtistSpotlight(models.Model):
    userid = models.IntegerField()
    artistid = models.IntegerField()
    blurb = models.TextField()
    date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'tma_artist_spotlight'


class TmaArtistStats(models.Model):
    userid = models.IntegerField()
    lastrun = models.DateTimeField()
    artist_modules = models.IntegerField()
    artist_total_downloads = models.BigIntegerField()
    artist_average_comment_score = models.DecimalField(max_digits=10, decimal_places=2)
    artist_average_review_score = models.DecimalField(max_digits=10, decimal_places=2)
    artist_total_reviews = models.IntegerField()
    artist_total_comments = models.IntegerField()
    artist_total_review_score = models.DecimalField(max_digits=10, decimal_places=1)
    artist_total_comment_score = models.DecimalField(max_digits=10, decimal_places=1)

    class Meta:
        managed = False
        db_table = 'tma_artist_stats'


class TmaBlacklist(models.Model):
    userid = models.IntegerField()
    type = models.TextField()
    data = models.CharField(unique=True, max_length=255)
    date = models.DateTimeField()
    hits = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tma_blacklist'


class TmaBotMessagesLegacy(models.Model):
    poster = models.TextField()
    msgtype = models.TextField()
    global_field = models.CharField(db_column='global', max_length=1)  # Field renamed because it was a Python reserved word.
    msgtext = models.TextField()
    msgexpired = models.CharField(max_length=1)
    posterip = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_bot_messages_legacy'


class TmaChartArtists(models.Model):
    userid = models.IntegerField()
    chart_magic = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tma_chart_artists'


class TmaChartDownloads(models.Model):
    moduleid = models.IntegerField(unique=True)
    chart_downloads_module = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tma_chart_downloads'


class TmaChartDownloadsScore(models.Model):
    moduleid = models.IntegerField()
    chart_module_rating_high = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'tma_chart_downloads_score'


class TmaCommentScores(models.Model):
    hash = models.CharField(primary_key=True, max_length=33)
    score = models.DecimalField(max_digits=10, decimal_places=1)
    totalcom = models.IntegerField()
    comment_score = models.DecimalField(max_digits=10, decimal_places=1)
    comment_total = models.IntegerField()
    review_score = models.DecimalField(max_digits=10, decimal_places=1)
    review_total = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tma_comment_scores'


class TmaComments(models.Model):
    moduleid = models.IntegerField()
    hash = models.TextField()
    userid = models.IntegerField()
    ipaddress = models.TextField()
    comment_text = models.TextField()
    comment_rating = models.DecimalField(max_digits=10, decimal_places=1)
    comment_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'tma_comments'


class TmaConfig(models.Model):
    config_tree = models.TextField()
    default_style = models.TextField()
    site_maintenance = models.IntegerField()
    points_earn_modupload = models.IntegerField()
    points_earn_review = models.IntegerField()
    points_earn_comment = models.IntegerField()
    path_http_download = models.TextField()
    path_file_archive_root = models.TextField()
    path_upload_queue_http = models.TextField()
    path_upload_queue_root = models.TextField()
    path_api_root = models.TextField()
    path_api_http = models.TextField()
    path_api_script_index = models.TextField()
    path_website_root = models.TextField()
    path_website_http = models.TextField()
    path_website_script_index = models.TextField()
    path_image_http = models.TextField()
    path_temp = models.TextField()
    path_lang = models.TextField()
    var_cookie_host = models.TextField()
    var_owner_uid = models.TextField()
    var_owner_gid = models.TextField()
    mirror_sync_delay = models.IntegerField()
    email_from_name = models.TextField()
    email_from_addr = models.TextField()
    max_filesize_archive = models.IntegerField()
    max_filesize_individual = models.IntegerField()
    path_bin_md5 = models.TextField()
    path_bin_gzip = models.TextField()
    path_bin_zip = models.TextField()
    path_bin_unzip = models.TextField()
    path_bin_cat = models.TextField()
    path_bin_modinfo = models.TextField()
    path_bin_mktemp = models.TextField()
    path_bin_chmod = models.TextField()
    quota_page_warn = models.IntegerField()
    quota_page_ban = models.IntegerField()
    quota_download_warn = models.IntegerField()
    quota_download_ban = models.IntegerField()
    irc_bot_host = models.TextField()
    irc_bot_port = models.IntegerField()
    irc_bot_operations_channel = models.TextField()
    irc_bot_public_channel = models.TextField()
    supported_formats = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_config'


class TmaContent(models.Model):
    pagename = models.CharField(primary_key=True, max_length=100)
    userid = models.IntegerField()
    locked = models.CharField(max_length=1)
    version = models.IntegerField()
    flags = models.IntegerField()
    author = models.CharField(max_length=100, blank=True, null=True)
    lastmodified = models.IntegerField()
    created = models.IntegerField()
    content = models.TextField()
    refs = models.TextField(blank=True, null=True)
    dateadded = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'tma_content'


class TmaContentLog(models.Model):
    userid = models.IntegerField()
    pagename = models.TextField()
    content = models.TextField()
    date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'tma_content_log'


class TmaCronCommonQueries(models.Model):
    time = models.DateTimeField()
    online_status = models.IntegerField()
    count_size = models.BigIntegerField()
    count_files = models.IntegerField()
    count_filehits = models.BigIntegerField()
    count_artists = models.IntegerField()
    count_crew = models.IntegerField()
    count_reviews = models.IntegerField()
    count_users = models.IntegerField()
    count_pending_accounts = models.IntegerField()
    count_newdir = models.IntegerField()
    count_comments = models.IntegerField()
    count_reviewers = models.IntegerField()
    count_board_posts = models.IntegerField()
    count_board_topics = models.IntegerField()
    count_chat_users = models.IntegerField()
    top_screeners = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_cron_common_queries'


class TmaDonationsLegacy(models.Model):
    visible = models.CharField(max_length=1)
    type = models.CharField(max_length=10)
    date = models.DateTimeField()
    name = models.TextField()
    nick = models.TextField()
    link = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'tma_donations_legacy'


class TmaDonationsPaypal(models.Model):
    ip = models.CharField(max_length=255)
    txn_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    dnuid = models.CharField(max_length=255)
    donation = models.DecimalField(max_digits=6, decimal_places=2)
    fees = models.DecimalField(max_digits=6, decimal_places=2)
    time = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tma_donations_paypal'


class TmaFavourites(models.Model):
    moduleid = models.IntegerField()
    filename = models.CharField(max_length=80)
    title = models.CharField(max_length=128)
    userid = models.IntegerField()
    date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'tma_favourites'


class TmaFilesLicenses(models.Model):
    moduleid = models.IntegerField()
    userid = models.IntegerField()
    license = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_files_licenses'


class TmaFilesRejected(models.Model):
    filename = models.CharField(max_length=60)
    uploader_uid = models.IntegerField()
    hash = models.CharField(max_length=33)
    filterer = models.CharField(max_length=60)
    reason = models.TextField()
    daterejected = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'tma_files_rejected'


class TmaFilesUploader(models.Model):
    userid = models.IntegerField(primary_key=True)
    moduleid = models.IntegerField(unique=True)

    class Meta:
        managed = False
        db_table = 'tma_files_uploader'
        unique_together = (('userid', 'moduleid'),)


class TmaImages(models.Model):
    type = models.TextField()
    title = models.TextField()
    link = models.TextField()
    image = models.TextField()
    image_mime = models.TextField()
    imagetype = models.TextField()
    hits = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tma_images'


class TmaLicenses(models.Model):
    licenseid = models.TextField()
    title = models.TextField()
    description = models.TextField()
    imageurl = models.TextField()
    deedurl = models.TextField()
    legalurl = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_licenses'


class TmaLogDownloads(models.Model):
    ip_address = models.CharField(max_length=15)
    last_request = models.DateTimeField()
    requests = models.IntegerField()
    bounces = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tma_log_downloads'


class TmaLogEditComment(models.Model):
    action = models.TextField()
    hash = models.CharField(max_length=34)
    userid = models.IntegerField()
    date = models.DateTimeField()
    oldcomment = models.TextField()
    ipaddress = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_log_edit_comment'


class TmaLogPageloads(models.Model):
    ip_address = models.CharField(primary_key=True, max_length=16)
    last_request = models.DateTimeField()
    requests = models.IntegerField()
    bounces = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tma_log_pageloads'


class TmaLogProfileComments(models.Model):
    poster_id = models.IntegerField()
    recipient_id = models.IntegerField()
    date = models.DateTimeField()
    ip_address = models.TextField()
    content = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_log_profile_comments'


class TmaMemberPoints(models.Model):
    userid = models.IntegerField()
    points_total = models.BigIntegerField()
    points_spent = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'tma_member_points'


class TmaMemberPointsBonus(models.Model):
    userid = models.IntegerField()
    points = models.IntegerField()
    date = models.DateTimeField()
    givenby = models.IntegerField()
    reason = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_member_points_bonus'


class TmaMemberStats(models.Model):
    userid = models.IntegerField()
    profile_views = models.BigIntegerField()
    comments_posted = models.IntegerField()
    reviews_posted = models.IntegerField()
    modules_uploaded = models.IntegerField()
    points = models.BigIntegerField()
    favourites = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tma_member_stats'


class TmaMirrors(models.Model):
    alias = models.CharField(max_length=40)
    sponsor_url = models.CharField(max_length=80)
    show_sponsor = models.IntegerField()
    image = models.TextField()
    image_mime = models.TextField()
    weight = models.IntegerField()
    path = models.TextField()
    contact = models.TextField()
    type = models.CharField(max_length=5)
    active = models.CharField(max_length=1)
    lockdown = models.CharField(max_length=1)
    activeformats = models.TextField()
    protocol = models.TextField()
    host = models.TextField()
    port = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tma_mirrors'


class TmaNominations(models.Model):
    hash = models.CharField(unique=True, max_length=33)
    userid = models.IntegerField()
    username = models.CharField(max_length=60)
    date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'tma_nominations'


class TmaProcessQueue(models.Model):
    data = models.IntegerField()
    userid = models.IntegerField()
    type = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_process_queue'


class TmaProfileComments(models.Model):
    profile_userid = models.IntegerField()
    poster_userid = models.IntegerField()
    is_reply = models.IntegerField()
    reply_to = models.IntegerField()
    reply_to_userid = models.IntegerField()
    date = models.DateTimeField()
    text = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_profile_comments'


class TmaRedirects(models.Model):
    redirect_from = models.IntegerField(unique=True, primary_key=True)
    redirect_to = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tma_redirects'


class TmaReviews(models.Model):
    moduleid = models.IntegerField()
    hash = models.TextField()
    userid = models.IntegerField()
    pending = models.IntegerField()
    pending_screening = models.IntegerField()
    rejection_text = models.TextField()
    incomplete = models.IntegerField()
    review_1 = models.TextField()
    review_r1 = models.DecimalField(max_digits=10, decimal_places=1)
    review_2 = models.TextField()
    review_r2 = models.DecimalField(max_digits=10, decimal_places=1)
    review_3 = models.TextField()
    review_r3 = models.DecimalField(max_digits=10, decimal_places=1)
    review_4 = models.TextField()
    review_r4 = models.DecimalField(max_digits=10, decimal_places=1)
    review_5 = models.TextField()
    review_r5 = models.DecimalField(max_digits=10, decimal_places=1)
    review_6 = models.TextField()
    review_r6 = models.DecimalField(max_digits=10, decimal_places=1)
    date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'tma_reviews'


class TmaSystems(models.Model):
    subsystem = models.CharField(max_length=30)
    locked = models.IntegerField()
    status = models.CharField(max_length=1)
    description = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_systems'


class TmaTags(models.Model):
    hash = models.CharField(max_length=33)
    tag = models.TextField()
    userid = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tma_tags'


class TmaTempData(models.Model):
    data1 = models.BigIntegerField()
    data2 = models.BigIntegerField()
    data3 = models.BigIntegerField()
    data4 = models.BigIntegerField()
    data5 = models.BigIntegerField()
    data6 = models.TextField()
    data7 = models.TextField()
    data8 = models.TextField()
    data9 = models.TextField()
    data10 = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_temp_data'


class TmaTriviaLegacy(models.Model):
    id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=5)
    trivia = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_trivia_legacy'


class TmaUsersActivation(models.Model):
    date = models.DateTimeField()
    ipaddress = models.TextField()
    userid = models.IntegerField()
    username = models.TextField()
    profile_fullname = models.TextField()
    email = models.TextField()
    password_enc = models.TextField()
    confirm_code = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_users_activation'


class TmaUsersBlock(models.Model):
    userid = models.IntegerField()
    block_userid = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tma_users_block'


class TmaUsersConfirmation(models.Model):
    date = models.DateTimeField()
    ipaddress = models.TextField()
    userid = models.IntegerField()
    username = models.TextField()
    password_text = models.TextField()
    confirm_code = models.TextField()

    class Meta:
        managed = False
        db_table = 'tma_users_confirmation'


class TmaXmlKeys(models.Model):
    xmlkey = models.CharField(unique=True, max_length=64)
    access_level = models.IntegerField()
    max_monthly_requests = models.IntegerField()
    owner = models.TextField()
    site = models.TextField()
    expiry = models.DateTimeField()
    last_access = models.DateTimeField()
    ip = models.TextField()
    requests = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tma_xml_keys'


class TmaXmlKeysLog(models.Model):
    xmlkey = models.CharField(max_length=64)
    requests = models.IntegerField()
    date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'tma_xml_keys_log'


class Users(models.Model):
    userid = models.AutoField(primary_key=True)
    username = models.CharField(unique=True, max_length=60)
    profile_censor = models.IntegerField()
    cred_member = models.CharField(max_length=1)
    cred_artist = models.CharField(max_length=1)
    cred_reviewer = models.CharField(max_length=1)
    cred_admin = models.CharField(max_length=1)
    cred_filterer = models.CharField(max_length=1)
    cred_trusted = models.CharField(max_length=1)
    cred_compobot = models.CharField(max_length=1)
    cred_helper = models.CharField(max_length=1)
    profile_email = models.CharField(max_length=255)
    profile_showemail = models.IntegerField()
    cred_crew = models.CharField(max_length=1)
    profile_password = models.TextField()
    profile_fullname = models.TextField()
    profile_blurb = models.TextField()
    profile_web = models.TextField()
    profile_theme = models.CharField(max_length=2, blank=True, null=True)
    profile_mimetype = models.TextField()
    profile_picture = models.TextField()
    profile_thumb = models.TextField()
    profile_icon = models.TextField()
    profile_picture_lastmodified = models.DateTimeField()
    profile_donated = models.IntegerField()
    profile_notifications = models.IntegerField()
    profile_shout_notifications = models.IntegerField()
    profile_shoutwall_status = models.IntegerField()
    favourite_views = models.IntegerField()
    site_minibox_status = models.IntegerField()
    site_details_status = models.IntegerField()
    date = models.DateTimeField()
    lastlogin = models.DateTimeField()
    lastipaddress = models.TextField()
    status_filtering = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'users'
