import pyblish.api
import ftrack


@pyblish.api.log
class ExtractFtrack(pyblish.api.InstancePlugin):

    """ Creating any Asset or AssetVersion in Ftrack.
    """

    order = pyblish.api.ExtractorOrder
    label = 'Ftrack'

    def process(self, instance):

        # skipping instance if ftrackData isn't present
        if not instance.context.data.get('ftrackData'):
            self.log.info('No ftrackData present. Skipping this instance')
            return

        # skipping instance if ftrackComponents isn't present
        if not instance.data.get('ftrackComponents'):
            self.log.info('No ftrackComponents found. Skipping this instance')
            return

        ftrack_data = instance.context.data['ftrackData'].copy()
        task = ftrack.Task(ftrack_data['Task']['id'])
        parent = task.getParent()
        asset_data = None
        create_version = False

        # creating asset
        if instance.data['ftrackAssetCreate']:
            asset = None

            # creating asset from ftrackAssetName
            if instance.data.get('ftrackAssetName'):

                asset_name = instance.data['ftrackAssetName']

                if instance.data.get('ftrackAssetType'):
                    asset_type = instance.data['ftrackAssetType']
                else:
                    asset_type = ftrack_data['Task']['name']

                asset = parent.createAsset(name=asset_name,
                                           assetType=asset_type, task=task)

                msg = "Creating new asset cause ftrackAssetName"
                msg += " (\"%s\") doesn't exist." % asset_name
                self.log.info(msg)
            else:
                # creating a new asset
                asset_name = ftrack_data['Task']['type']
                asset_type = ftrack_data['Task']['code']
                asset = parent.createAsset(name=asset_type,
                                           assetType=asset_type, task=task)

                msg = "Creating asset cause no asset is present."
                self.log.info(msg)

            create_version = True
            # adding asset to ftrack data
            asset_data = {'id': asset.getId(),
                          'name': asset.getName()}

        if not asset_data:
            asset_data = instance.data['ftrackAsset']

        instance.data['ftrackAsset'] = asset_data

        # creating version
        version = None
        if instance.data['ftrackAssetVersionCreate'] or create_version:
            asset = ftrack.Asset(asset_data['id'])
            taskid = ftrack_data['Task']['id']
            version_number = int(instance.context.data['version'])

            version = self.GetVersionByNumber(asset, version_number)

            if not version:
                version = asset.createVersion(comment='', taskid=taskid)
                version.set('version', value=version_number)
                msg = 'Creating new asset version by %s.' % version_number
                self.log.info(msg)
            else:
                msg = 'Using existing asset version by %s.' % version_number
                self.log.info(msg)

            asset_version = {'id': version.getId(), 'number': version_number}
            instance.data['ftrackAssetVersion'] = asset_version
            version.publish()
        else:
            # using existing version
            asset_version = instance.data['ftrackAssetVersion']
            version = ftrack.AssetVersion(asset_version['id'])

        # adding asset version to ftrack data
        instance.data['ftrackAssetVersion'] = asset_version

    def GetVersionByNumber(self, asset, number):
        for version in asset.getVersions():
            try:
                if version.getVersion() == int(number):
                    return version
            except:
                return None
