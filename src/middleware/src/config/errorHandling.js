module.exports = {
    missing_fields: { tag: 'missing_fields', message: 'Mandatory fields were missing' },
    invalid_password_or_email: {
        tag: 'invalid_password_or_email',
        message: 'Invalid password or email',
    },
    email_already_registered: {
        tag: 'email_already_registered',
        message: 'This email has been registered already',
    },
    invalid_password_registration: {
        tag: 'invalid_password_registration',
        message: 'Password must contain 8 or more characters',
    },
    email_format_not_valid: {
        tag: 'email_format_not_valid',
        message: 'Does not look like an email',
    },
    system_error: { tag: 'system_error', message: 'Something bad happend' },
    token_expired: {
        tag: 'token_expired',
        message:
            'Token/Session does not exist, is invalid or is too old for proceeding. Please, generate a new one',
    },
    user_not_found: { tag: 'user_not_found', message: 'User does not exist' },
    invalid_credentials: { tag: 'invalid_credentials', message: 'Invalid email or password' },
    account_not_active: {
        tag: 'account_not_active',
        message:
            'Account is not yet active. Please check your email inbox and click the link to verify your account',
    },
    token_app_not_valid: { tag: 'token_app_not_valid', message: 'Token not valid or not found' },
    max_number_of_login_attempts: {
        tag: 'max_login_attempts',
        message: 'Max number of login attempts reached. Please, try again in a few hours',
    },
    max_number_of_registration_attempts: {
        tag: 'max_registration_attempts',
        message:
            'You registered or tried to register too many accounts. If that was a mistake, please: try again in a few hours',
    },

    taggedError: (tag, rewritableMessage = false) => {
        let message = rewritableMessage ? rewritableMessage : tag.message;
        return { error: tag.tag, message: message };
    },
};
