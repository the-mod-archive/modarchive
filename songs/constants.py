CLAIM_KEYWORD = 'claim'
CLAIM_DESCRIPTION = 'Claim for Screening'
CLAIM_ACTION = (CLAIM_KEYWORD, CLAIM_DESCRIPTION)

UNCLAIM_KEYWORD = 'unclaim'
UNCLAIM_DESCRIPTION = 'Unclaim'
UNCLAIM_ACTION = (UNCLAIM_KEYWORD, UNCLAIM_DESCRIPTION)

PRE_SCREEN_KEYWORD = 'pre_screen'
PRE_SCREEN_DESCRIPTION = 'Mark as Pre-Screened'
PRE_SCREEN_ACTION = (PRE_SCREEN_KEYWORD, PRE_SCREEN_DESCRIPTION)

PRE_SCREEN_AND_RECOMMEND_KEYWORD = 'pre_screen_and_recommend'
PRE_SCREEN_AND_RECOMMEND_DESCRIPTION = 'Mark as Pre-Screened, and Recommend for Featured Song'
PRE_SCREEN_AND_RECOMMEND_ACTION = (PRE_SCREEN_AND_RECOMMEND_KEYWORD, PRE_SCREEN_AND_RECOMMEND_DESCRIPTION)

APPROVE_KEYWORD = 'approve'
APPROVE_DESCRIPTION = 'Approve and Add to Archive'
APPROVE_ACTION = (APPROVE_KEYWORD, APPROVE_DESCRIPTION)

APPROVE_AND_FEATURE_KEYWORD = 'approve_and_feature'
APPROVE_AND_FEATURE_DESCRIPTION = 'Approve and Add to Archive as Featured Song'
APPROVE_AND_FEATURE_ACTION = (APPROVE_AND_FEATURE_KEYWORD, APPROVE_AND_FEATURE_DESCRIPTION)

NEEDS_SECOND_OPINION_KEYWORD = 'needs_second_opinion'
NEEDS_SECOND_OPINION_DESCRIPTION = 'Request a Second Opinion'
NEEDS_SECOND_OPINION_ACTION = (NEEDS_SECOND_OPINION_KEYWORD, NEEDS_SECOND_OPINION_DESCRIPTION)

POSSIBLE_DUPLICATE_KEYWORD = 'possible_duplicate'
POSSIBLE_DUPLICATE_DESCRIPTION = 'Report as Possible Duplicate'
POSSIBLE_DUPLICATE_ACTION = (POSSIBLE_DUPLICATE_KEYWORD, POSSIBLE_DUPLICATE_DESCRIPTION)

UNDER_INVESTIGATION_KEYWORD = 'under_investigation'
UNDER_INVESTIGATION_DESCRIPTION = 'Report as Under Investigation'
UNDER_INVESTIGATION_ACTION = (UNDER_INVESTIGATION_KEYWORD, UNDER_INVESTIGATION_DESCRIPTION)

REJECT_KEYWORD = 'reject'
REJECT_DESCRIPTION = 'Reject and Remove from Queue'
REJECT_ACTION = (REJECT_KEYWORD, REJECT_DESCRIPTION)

CLEAR_FLAG_KEYWORD = 'clear_flag'
CLEAR_FLAG_DESCRIPTION = 'Clear Flag and Return to Queue'
CLEAR_FLAG_ACTION = (CLEAR_FLAG_KEYWORD, CLEAR_FLAG_DESCRIPTION)

RENAME_KEYWORD = 'rename'
RENAME_DESCRIPTION = 'Change Filename for Song'
RENAME_ACTION = (RENAME_KEYWORD, RENAME_DESCRIPTION)

UNCLAIMED_GROUP = 'Unclaimed'
YOUR_REVIEW_GROUP = 'Your Claimed Songs'
NOT_YOUR_REVIEW_GROUP = 'Songs Claimed by Others'
READY_TO_BE_ADDED_GROUP = 'Ready to be Added'
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
PRE_SCREENED_AND_RECOMMENDED_FILTER_DESCRIPTION = 'Pre-Screened and Recommend for Featured Song'
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
MESSAGE_SONGS_APPROVED = '%s songs approved.'
MESSAGE_NO_SONGS_SELECTED = 'No songs selected.'

FLAG_MESSAGE_SECOND_OPINION = 'Another screener would like a second opinion on this song.'
FLAG_MESSAGE_POSSIBLE_DUPLICATE = 'This song may be a duplicate of another song in the database. Please verify.'
FLAG_MESSAGE_UNDER_INVESTIGATION = 'Do not approve. This song is under investigation. This flag must be cleared before song can be approved.'
FLAG_MESSAGE_PRE_SCREENED = 'This song has been pre-screened and can be added to the archive.'
FLAG_MESSAGE_PRE_SCREENED_AND_RECOMMENDED = 'This song has been pre-screened and is recommended to be a featured song. It can be added to the archive.'

REJECTION_REQUIRES_IDS = 'You must specify at least one song to reject.'
REJECTION_ALL_SONGS_MUST_BE_CLAIMED = 'You cannot reject a song that you have not claimed.'

RENAME_SCREENING_REQUIRES_CLAIM = 'You must claim a song before you can rename it.'
RENAME_SCREENING_ONE_SONG_ONLY = 'You can only rename one song at a time.'
RENAME_CANNOT_CHANGE_FILE_EXTENSION = 'You cannot change the file extension when renaming a song.'
RENAME_MUST_BE_CHANGED = 'The new filename must be different from the old filename.'
RENAME_INVALID_FILENAME = 'The new filename is invalid.'
RENAME_FILENAME_TAKEN = 'The new filename is already taken by another song in the archive.'
RENAME_FAILED = 'Something went wrong when renaming the file. Please try again. If failures continue, contact an administrator.'

UPLOAD_TOO_LARGE = 'The file was above the maximum allowed size of %s bytes.'
UPLOAD_FILENAME_TOO_LONG = 'The filename length was above the maximum allowed limit of %s characters.'
UPLOAD_UNRECOGNIZED_FORMAT = 'The file was not recognized as a valid module file.'
UPLOAD_UNSUPPORTED_FORMAT = 'This format is not currently supported.'
UPLOAD_DUPLICATE_SONG_IN_ARCHIVE = 'An identical song was already found in the archive.'
UPLOAD_DUPLICATE_SONG_IN_PROCESSING_QUEUE = 'An identical song was already found in the upload processing queue.'
UPLOAD_SONG_PREVIOUSLY_REJECTED = 'This song was previously rejected by screeners.'
