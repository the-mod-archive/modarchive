CLAIM_KEYWORD = 'claim'
CLAIM_DESCRIPTION = 'Claim for Screening'
CLAIM_ACTION = (CLAIM_KEYWORD, CLAIM_DESCRIPTION)

PRE_SCREEN_KEYWORD = 'pre_screen'
PRE_SCREEN_DESCRIPTION = 'Mark as Pre-Screened'
PRE_SCREEN_ACTION = (PRE_SCREEN_KEYWORD, PRE_SCREEN_DESCRIPTION)

PRE_SCREEN_AND_RECOMMEND_KEYWORD = 'pre_screen_and_recommend'
PRE_SCREEN_AND_RECOMMEND_DESCRIPTION = 'Mark as Pre-Screened, and Recommend for Featured Song'
PRE_SCREEN_AND_RECOMMEND_ACTION = (PRE_SCREEN_AND_RECOMMEND_KEYWORD, PRE_SCREEN_AND_RECOMMEND_DESCRIPTION)

APPROVE_KEYWORD = 'approve'
APPROVE_DESCRIPTION = 'Approve and Add to Archive'
APPROVE_ACTION = (APPROVE_KEYWORD, APPROVE_DESCRIPTION)

NEEDS_SECOND_OPINION_KEYWORD = 'needs_second_opinion'
NEEDS_SECOND_OPINION_DESCRIPTION = 'Request a Second Opinion'
NEEDS_SECOND_OPINION_ACTION = (NEEDS_SECOND_OPINION_KEYWORD, NEEDS_SECOND_OPINION_DESCRIPTION)

POSSIBLE_DUPLICATE_KEYWORD = 'possible_duplicate'
POSSIBLE_DUPLICATE_DESCRIPTION = 'Report as Possible Duplicate'
POSSIBLE_DUPLICATE_ACTION = (POSSIBLE_DUPLICATE_KEYWORD, POSSIBLE_DUPLICATE_DESCRIPTION)

UNDER_INVESTIGATION_KEYWORD = 'under_investigation'
UNDER_INVESTIGATION_DESCRIPTION = 'Report as Under Investigation'
UNDER_INVESTIGATION_ACTION = (UNDER_INVESTIGATION_KEYWORD, UNDER_INVESTIGATION_DESCRIPTION)

UNCLAIMED_GROUP = 'Unclaimed'
CLAIMED_GROUP = 'Claimed'
DONE_GROUP = 'Done'
FLAGGED_GROUP = 'Flagged'
HIGH_PRIORITY_FILTER = 'high_priority'
HIGH_PRIORITY_FILTER_DESCRIPTION = 'High Priority'
LOW_PRIORITY_FILTER = 'low_priority'
LOW_PRIORITY_FILTER_DESCRIPTION = 'Low Priority'
BY_UPLOADER_FILTER = 'by_uploader'
BY_UPLOADER_FILTER_DESCRIPTION = 'Uploaded by Artist'
MY_SCREENING_FILTER = 'my_screening'
MY_SCREENING_FILTER_DESCRIPTION = 'Songs I\'m Screening'
OTHERS_SCREENING_FILTER = 'others_screening'
OTHERS_SCREENING_FILTER_DESCRIPTION = 'Songs Others are Screening'
PRE_SCREENED_FILTER = 'pre_screened'
PRE_SCREENED_FILTER_DESCRIPTION = 'Pre-Screened'
PRE_SCREENED_AND_RECOMMENDED_FILTER = 'pre_screened_and_recommended'
PRE_SCREENED_AND_RECOMMENDED_FILTER_DESCRIPTION = 'Pre-Screened and Recommended'
NEEDS_SECOND_OPINION_FILTER = 'needs_second_opinion'
NEEDS_SECOND_OPINION_FILTER_DESCRIPTION = 'Needs Second Opinion'
POSSIBLE_DUPLICATE_FILTER = 'possible_duplicate'
POSSIBLE_DUPLICATE_FILTER_DESCRIPTION = 'Possible Duplicate'
UNDER_INVESTIGATION_FILTER = 'under_investigation'
UNDER_INVESTIGATION_FILTER_DESCRIPTION = 'Under Investigation (do not approve)'

MESSAGE_APPROVAL_REQUIRES_CLAIM = 'You must claim a song before you can approve it, or the song must be pre-screened.'
MESSAGE_CANNOT_APPROVE_UNDER_INVESTIGATION = 'You cannot approve a song that is under investigation.'
MESSAGE_CANNOT_APPROVE_POSSIBLE_DUPLICATE = 'You cannot approve a song that is a possible duplicate.'
MESSAGE_CANNOT_APPROVE_DUPLICATE_FILENAME = 'A song with this filename already exists in the archive. You will need to change the filename before it can be approved.'
MESSAGE_CANNOT_APPROVE_DUPLICATE_HASH = 'A song with this hash already exists in the archive.'
MESSAGE_ALL_SONGS_MUST_BE_PRESCREENED_FOR_BULK_APPROVAL = 'All songs must be pre-screened before they can be bulk approved.'
MESSAGE_ALL_SONGS_MUST_HAVE_UNIQUE_FILENAME_FOR_BULK_APPROVAL = 'All songs must have a unique filename before they can be bulk approved.'
MESSAGE_ALL_SONGS_MUST_HAVE_UNIQUE_HASH_FOR_BULK_APPROVAL = 'All songs must have a unique hash before they can be bulk approved.'
MESSAGE_ALL_SONGS_MUST_NOT_BE_CLAIMED_BY_OTHERS_FOR_BULK_APPROVAL = 'You cannot bulk approve if any song is claimed by somebody else.'

FLAG_MESSAGE_SECOND_OPINION = 'Another screener would like a second opinion on this song.'
FLAG_MESSAGE_POSSIBLE_DUPLICATE = 'This song may be a duplicate of another song in the database. Please verify.'
FLAG_MESSAGE_UNDER_INVESTIGATION = 'Do not approve. This song is under investigation. This flag must be cleared before song can be approved.'
FLAG_MESSAGE_PRE_SCREENED = 'This song has been pre-screened and can be added to the archive.'
FLAG_MESSAGE_PRE_SCREENED_AND_RECOMMENDED = 'This song has been pre-screened and is recommended to be a featured song. It can be added to the archive.'
