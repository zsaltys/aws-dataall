import logging

from sqlalchemy.sql import and_

from .. import exceptions, permissions, paginate
from .. import models
from ..api.permission import Permission
from ..api.tenant import Tenant
from ..models.Permission import PermissionType

logger = logging.getLogger(__name__)


# def _fix_json_array(obj, attr):
#     arr = getattr(obj, attr)
#     if isinstance(arr, list) and len(arr) > 1 and arr[0] == '{':
#         arr = arr[1:-1]
#         arr = ''.join(arr).split(",")
#         setattr(obj, attr, arr)


class LFTag:
    @staticmethod
    def list_tenant_lf_tags(session, username, groups, uri, data=None, check_perm=None):
        query = session.query(models.LFTag)

        if data and data.get('term'):
            query = query.filter(
                models.LFTag.LFTagKey.ilike('%' + data.get('term') + '%')
            )
        result = paginate(
            query=query,
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

        # for item in result["nodes"]:
        #     _fix_json_array(item, 'LFTagValues')

        return result

    @staticmethod
    def list_all_lf_tags(session):
        lftags = session.query(models.LFTag).all()

        # for item in lftags:
        #     _fix_json_array(item, 'LFTagValues')

        return lftags

    @staticmethod
    def remove_lf_tag(session, username, groups, uri, check_perm=None):
        if not uri:
            raise exceptions.RequiredParameter('lftagUri')

        lf_tag = LFTag.get_lf_tag_by_uri(session, uri)

        if lf_tag:
            session.delete(lf_tag)
            session.commit()

        return True

    @staticmethod
    def get_lf_tag_by_uri(session, uri):
        lftag = session.query(models.LFTag).filter(
            models.LFTag.lftagUri == uri
        ).first()

        if not lftag:
            raise exceptions.ObjectNotFound(
                'LFTagUri', f'({uri})'
            )
        return lftag

    @staticmethod
    def get_lf_tag_by_name(session, lf_tag_key):
        return session.query(models.LFTag).filter(
            models.LFTag.LFTagKey == lf_tag_key
        ).first()

    @staticmethod
    def add_lf_tag(session, username, groups, data, check_perm=None):
        lf_tag_key: str = data['LFTagKey']

        alreadyAdded = LFTag.get_lf_tag_by_name(
            session, lf_tag_key
        )
        if alreadyAdded:
            raise exceptions.UnauthorizedOperation(
                action='ADD_LF_TAG',
                message=f'LF Tag {lf_tag_key} already exists',
            )

        lf_tag = models.LFTag(
            LFTagKey=data['LFTagKey'],
            LFTagValues=data.get('LFTagValues', []),
            description=data.get('description'),
            owner="DAAdministrators"

        )

        session.add(lf_tag)
        session.commit()
        return lf_tag


class LFTagPermissions:
    @staticmethod
    def list_tenant_lf_tag_permissions(session, username, groups, uri, data=None, check_perm=None):
        query = session.query(models.LFTagPermissions)

        if data and data.get('term'):
            query = query.filter(
                models.LFTagPermissions.tagKey.ilike('%' + data.get('term') + '%')
            )
        result = paginate(
            query=query,
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

        # for item in result["nodes"]:
        #     _fix_json_array(item, 'tagValues')

        return result

    # @staticmethod
    # def update_lftag_permissions_if_not_exist(
    #     session, username, group, tagkey, tagval
    # ) -> dict:
        
    #     lf_permission = (
    #         session.query(models.LFTagPermissions)
    #         .filter(
    #             and_(
    #                 models.LFTagPermissions.SamlGroupName==group,
    #                 models.LFTagPermissions.tagKey==tagkey,
    #                 models.LFTagPermissions.tagValues.contains(f'{{{tagkey}}}'),
    #             )
    #         )
    #         .first()
    #     )
        
        # if not lf_permission:
        #     lf_tag_permission =models.LFTagPermissions(
        #         SamlGroupName=owner,
        #         environmentUri=env.environmentUri,
        #         environmentLabel=env.label,
        #         awsAccount=env.AwsAccountId,
        #         tagKey=tagkey,
        #         tagValues=tagval
        #     )
        #     session.add(lf_tag_permission)

        # return lf_tag_permission

    # @staticmethod
    # def query_lf_tags_all(session, username, groups, uri):
    #     query = (
    #         session.query(models.LFTagPermissions)
    #         .filter(
    #             and_(
    #                 models.LFTagPermissions.SamlGroupName.in_(groups),
    #                 models.LFTagPermissions.environmentUri == uri
    #             )
    #         )
    #     )
    #     return query