# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

def convert_text_into_dict(temp_value):
    if isinstance(temp_value, str):
        return {'value': temp_value}
    else:
        return temp_value


def transform(logdata):
    if 'errorCode' in logdata or 'errorMessage' in logdata:
        logdata['event']['outcome'] = 'failure'
    else:
        logdata['event']['outcome'] = 'success'
    try:
        name = logdata['user']['name']
        if ':' in name:
            logdata['user']['name'] = name.split(':')[-1].split('/')[-1]
    except KeyError:
        pass

    # https://github.com/aws-samples/siem-on-amazon-elasticsearch/issues/33
    try:
        response_cred = logdata['responseElements']['credentials']
    except (KeyError, TypeError):
        response_cred = None
    if isinstance(response_cred, str):
        logdata['responseElements']['credentials'] = {}
        if 'arn:aws:iam' in response_cred:
            logdata['responseElements']['credentials']['iam'] = response_cred
        else:
            logdata['responseElements']['credentials']['value'] = response_cred

    # https://github.com/aws-samples/siem-on-amazon-elasticsearch/issues/108
    try:
        logdata['requestParameters']['tags'] = convert_text_into_dict(
            logdata['requestParameters']['tags'])
    except (KeyError, TypeError):
        pass

    # https://github.com/aws-samples/siem-on-amazon-elasticsearch/issues/114
    try:
        logdata['responseElements']['policy'] = convert_text_into_dict(
            logdata['responseElements']['policy'])
    except (KeyError, TypeError):
        pass

    # https://github.com/aws-samples/siem-on-amazon-elasticsearch/issues/139
    try:
        logdata['requestParameters']['disableApiTermination'] = (
            logdata['requestParameters']['disableApiTermination']['value'])
    except (KeyError, TypeError):
        pass

    event_source = logdata.get('eventSource', None)
    if event_source == 'athena.amazonaws.com':
        # #153
        try:
            tableMetadataList = (
                logdata['responseElements']['tableMetadataList'])
        except (KeyError, TypeError):
            tableMetadataList = None
        if tableMetadataList:
            for tableMetadata in tableMetadataList:
                old_field = 'projection.date.interval.unit'
                new_field = 'projection.date.interval_unit'
                try:
                    tableMetadata['parameters'][new_field] = (
                        tableMetadata['parameters'].pop(old_field))
                except KeyError:
                    pass
    elif event_source == 'glue.amazonaws.com':
        # #156
        try:
            configuration = logdata['requestParameters']['configuration']
        except KeyError:
            configuration = None
        if configuration and isinstance(configuration, str):
            logdata['requestParameters']['configuration'] = {
                'text': configuration}

    return logdata
