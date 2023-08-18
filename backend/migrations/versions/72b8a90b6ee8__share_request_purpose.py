"""_share_request_purpose

Revision ID: 72b8a90b6ee8
Revises: 509997f0a51e
Create Date: 2023-06-05 12:28:56.221364

"""
from alembic import op
from sqlalchemy import orm, Column, String, and_
from sqlalchemy.ext.declarative import declarative_base

from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.db.resource_policy_repositories import ResourcePolicy
from dataall.modules.dataset_sharing.db.share_object_models import ShareObject
from dataall.modules.dataset_sharing.services.share_permissions import SHARE_OBJECT_APPROVER, SHARE_OBJECT_REQUESTER
from dataall.modules.datasets_base.db.dataset_repositories import DatasetRepository

# revision identifiers, used by Alembic.
revision = '72b8a90b6ee8'
down_revision = '509997f0a51e'
branch_labels = None
depends_on = None

Base = declarative_base()


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('share_object', Column('requestPurpose', String(), nullable=True))
    op.add_column('share_object', Column('rejectPurpose', String(), nullable=True))

    # ### Fix Permissions Set for Share Object Approvers + Requesters
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        print('Getting all Share Objects...')
        shares: [ShareObject] = session.query(ShareObject).all()
        for share in shares:
            dataset = DatasetRepository.get_dataset_by_uri(session, share.datasetUri)
            environment = EnvironmentService.get_environment_by_uri(session, share.environmentUri)

            # Env Admins
            # Delete Share Object Permissions on Share Env Admin if Not Share Requester Group
            if share.groupUri != environment.SamlGroupName:
                ResourcePolicy.delete_resource_policy(
                    session=session,
                    group=environment.SamlGroupName,
                    resource_uri=share.shareUri,
                )
                print(f"Delete SHARE_OBJECT Permissions for Env Owner {environment.SamlGroupName} on Share {share.shareUri}")

            # Dataset Admins
            # Delete and Recreate Dataset Share Object Permissions to be Share Object Approver Permission Set
            ResourcePolicy.delete_resource_policy(
                session=session,
                group=dataset.SamlAdminGroupName,
                resource_uri=share.shareUri,
            )
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=dataset.SamlAdminGroupName,
                permissions=SHARE_OBJECT_APPROVER,
                resource_uri=share.shareUri,
                resource_type=ShareObject.__name__,
            )
            print(f"Recreated SHARE_OBJECT_APPROVER Permissions for Dataset Owner {dataset.SamlAdminGroupName} on Share {share.shareUri}")

            # Dataset Stewards
            # Delete and Recreate Dataset Share Object Permissions to be Share Object Approver Permission Set
            if dataset.SamlAdminGroupName != dataset.stewards:
                ResourcePolicy.delete_resource_policy(
                    session=session,
                    group=dataset.stewards,
                    resource_uri=share.shareUri,
                )
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=dataset.stewards,
                    permissions=SHARE_OBJECT_APPROVER,
                    resource_uri=share.shareUri,
                    resource_type=ShareObject.__name__,
                )
                print(f"Recreated SHARE_OBJECT_APPROVER Permissions for Dataset Steward {dataset.stewards} on Share {share.shareUri}")

    except Exception as e:
        print(e)
        print(f'Failed to update share object approver permissions due to: {e}')
        raise e
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        print('Getting all Share Objects...')
        shares: [ShareObject] = session.query(ShareObject).all()
        for share in shares:
            dataset = DatasetRepository.get_dataset_by_uri(session, share.datasetUri)
            environment = EnvironmentService.get_environment_by_uri(session, share.environmentUri)

            # Env Admins
            # Add SHARE_OBJECT_REQUESTER to Env Admin Group
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=environment.SamlGroupName,
                permissions=SHARE_OBJECT_REQUESTER,
                resource_uri=share.shareUri,
                resource_type=ShareObject.__name__,
            )
            print(f"Adding SHARE_OBJECT_REQUESTER Permissions for Share Env Admin {environment.SamlGroupName} on Share {share.shareUri}")

            # Dataset Admins
            # Remove SHARE_OBJECT_APPROVER Permissions if Exists Separate from Stewards(i.e. if steward != owner)
            # Add SHARE_OBJECT_REQUESTER Permissions to Dataset Admin Group
            if dataset.SamlAdminGroupName != dataset.stewards:
                ResourcePolicy.delete_resource_policy(
                    session=session,
                    group=dataset.SamlAdminGroupName,
                    resource_uri=share.shareUri,
                )
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=dataset.SamlAdminGroupName,
                permissions=SHARE_OBJECT_REQUESTER,
                resource_uri=share.shareUri,
                resource_type=ShareObject.__name__,
            )
            print(f"Adding SHARE_OBJECT_REQUESTER Permissions for Dataset Owner {dataset.SamlAdminGroupName} on Share {share.shareUri}")
    except Exception as e:
        print(e)
        print(f'Failed to update share object approver permissions due to: {e}')
        raise e

    op.drop_column('share_object', 'requestPurpose')
    op.drop_column('share_object', 'rejectPurpose')
    # ### end Alembic commands ###
