import pyblish.api
import ftrack


@pyblish.api.log
class IntegrateFtrack(pyblish.api.InstancePlugin):

    """ Creating Components in Ftrack.
    """

    order = pyblish.api.IntegratorOrder + 0.11
    label = 'Ftrack'
    optional = True

    def process(self, instance):

        # skipping instance if ftrackData isn't present
        if 'ftrackData' not in instance.context.data:
            self.log.info('No ftrackData present. Skipping this instance')
            return

        # skipping instance if ftrackComponents isn't present
        if 'ftrackComponents' not in instance.data:
            self.log.info('No ftrackComponents present\
                           Skipping this instance')
            return

        asset_version = instance.data['ftrackAssetVersion']
        version = ftrack.AssetVersion(asset_version['id'])

        # creating comment
        comment = instance.context.data.get('comment')
        if comment:
            version.set('comment', value=comment)

        # creating components
        components = instance.data['ftrackComponents']
        for component_name in instance.data['ftrackComponents']:

            # creating component
            try:
                path = components[component_name]['path']
            except:
                return

            component = None
            try:
                component = version.createComponent(name=component_name,
                                                    path=path)
                self.log.info('Creating "%s" component.' % component_name)
            except:
                component = version.getComponent(name=component_name)
                msg = "Component \"%s\" exists," % component_name
                msg += " nothing was changed."
                self.log.info(msg)

            cid = component.getId()
            instance.data["ftrackComponents"][component_name]["id"] = cid

            # make reviewable
            if 'reviewable' in components[component_name]:
                upload = True
                for component in version.getComponents():
                    if component_name in ('ftrackreview-mp4',
                                          'ftrackreview-webm'):
                        upload = False
                        break
                if upload:
                    ftrack.Review.makeReviewable(version, path)
