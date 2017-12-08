
from __future__ import absolute_import, division, print_function, \
    unicode_literals

import xarray as xr

from ..shared import AnalysisTask

from ..shared.climatology import RemapMpasClimatologySubtask, \
    RemapObservedClimatologySubtask

from .plot_climatology_map_subtask import PlotClimatologyMapSubtask

from ..shared.io.utility import build_config_full_path

from ..shared.grid import LatLonGridDescriptor


class ClimatologyMapSeaIceConc(AnalysisTask):  # {{{
    """
    An analysis task for comparison of sea ice concentration against
    observations

    Authors
    -------
    Luke Van Roekel, Xylar Asay-Davis, Milena Veneziani
    """
    def __init__(self, config, mpasClimatologyTask, hemisphere):
        # {{{
        """
        Construct the analysis task.

        Parameters
        ----------
        config :  instance of MpasAnalysisConfigParser
            Contains configuration options

        mpasClimatologyTask : ``MpasClimatologyTask``
            The task that produced the climatology to be remapped and plotted

        hemisphere : {'NH', 'SH'}
            The hemisphere to plot

        Authors
        -------
        Xylar Asay-Davis
        """
        taskName = 'climatologyMapSeaIceConc{}'.format(hemisphere)

        self.fieldName = 'seaIceConc'
        # call the constructor from the base class (AnalysisTask)
        super(ClimatologyMapSeaIceConc, self).__init__(
                config=config, taskName=taskName,
                componentName='seaIce',
                tags=['climatology', 'horizontalMap', self.fieldName])

        mpasFieldName = 'timeMonthly_avg_iceAreaCell'
        iselValues = None

        sectionName = taskName

        if hemisphere == 'NH':
            hemisphereLong = 'Northern'
        else:
            hemisphereLong = 'Southern'

        obsFieldName = 'seaIceConc'

        # read in what seasons we want to plot
        seasons = config.getExpression(sectionName, 'seasons')

        if len(seasons) == 0:
            raise ValueError('config section {} does not contain valid list '
                             'of seasons'.format(sectionName))

        comparisonGridNames = config.getExpression(sectionName,
                                                   'comparisonGrids')

        if len(comparisonGridNames) == 0:
            raise ValueError('config section {} does not contain valid list '
                             'of comparison grids'.format(sectionName))

        # the variable self.mpasFieldName will be added to mpasClimatologyTask
        # along with the seasons.
        remapClimatologySubtask = RemapMpasClimatologySubtask(
            mpasClimatologyTask=mpasClimatologyTask,
            parentTask=self,
            climatologyName='{}{}'.format(self.fieldName, hemisphere),
            variableList=[mpasFieldName],
            comparisonGridNames=comparisonGridNames,
            seasons=seasons,
            iselValues=iselValues)

        observationPrefixes = config.getExpression(sectionName,
                                                   'observationPrefixes')
        for prefix in observationPrefixes:
            for season in seasons:
                observationTitleLabel = \
                    'Observations (SSM/I {})'.format(prefix)

                obsFileName = build_config_full_path(
                        config, 'seaIceObservations',
                        'concentration{}{}_{}'.format(prefix,
                                                      hemisphere,
                                                      season))

                remapObservationsSubtask = RemapObservedConcClimatology(
                        parentTask=self, seasons=[season],
                        fileName=obsFileName,
                        outFilePrefix='{}{}{}_{}'.format(obsFieldName, prefix,
                                                         hemisphere, season),
                        comparisonGridNames=comparisonGridNames,
                        subtaskName='remapObservations_{}{}'.format(prefix,
                                                                    season))
                self.add_subtask(remapObservationsSubtask)
                for comparisonGridName in comparisonGridNames:

                    imageDescription = \
                        '{} Climatology Map of {}-Hemisphere Sea-Ice ' \
                        'Concentration'.format(season, hemisphereLong)
                    imageCaption = '{}. <br> Observations: SSM/I {}'.format(
                        imageDescription, prefix)
                    galleryGroup = \
                        '{}-Hemisphere Sea-Ice Concentration'.format(
                                hemisphereLong)
                    # make a new subtask for this season and comparison grid
                    subtask = PlotClimatologyMapSubtask(
                            self, hemisphere, season, comparisonGridName,
                            remapClimatologySubtask, remapObservationsSubtask,
                            subtaskSuffix=prefix)

                    subtask.set_plot_info(
                            outFileLabel='iceconc{}{}'.format(prefix,
                                                              hemisphere),
                            fieldNameInTitle='Sea ice concentration',
                            mpasFieldName=mpasFieldName,
                            obsFieldName=obsFieldName,
                            observationTitleLabel=observationTitleLabel,
                            unitsLabel=r'fraction',
                            imageDescription=imageDescription,
                            imageCaption=imageCaption,
                            galleryGroup=galleryGroup,
                            groupSubtitle=None,
                            groupLink='{}_conc'.format(hemisphere.lower()),
                            galleryName='Observations: SSM/I {}'.format(
                                    prefix))

                    self.add_subtask(subtask)
        # }}}
    # }}}


class RemapObservedConcClimatology(RemapObservedClimatologySubtask):  # {{{
    """
    A subtask for reading and remapping sea ice concentration observations

    Authors
    -------
    Xylar Asay-Davis
    """

    def get_observation_descriptor(self, fileName):  # {{{
        '''
        get a MeshDescriptor for the observation grid

        Parameters
        ----------
        fileName : str
            observation file name describing the source grid

        Returns
        -------
        obsDescriptor : ``MeshDescriptor``
            The descriptor for the observation grid

        Authors
        -------
        Xylar Asay-Davis
        '''

        # create a descriptor of the observation grid using the lat/lon
        # coordinates
        obsDescriptor = LatLonGridDescriptor.read(fileName=fileName,
                                                  latVarName='t_lat',
                                                  lonVarName='t_lon')
        return obsDescriptor  # }}}

    def build_observational_dataset(self, fileName):  # {{{
        '''
        read in the data sets for observations, and possibly rename some
        variables and dimensions

        Parameters
        ----------
        fileName : str
            observation file name

        Returns
        -------
        dsObs : ``xarray.Dataset``
            The observational dataset

        Authors
        -------
        Xylar Asay-Davis
        '''

        dsObs = xr.open_dataset(fileName)
        dsObs.rename({'AICE': 'seaIceConc'}, inplace=True)
        return dsObs
        # }}}
    # }}}


# vim: foldmethod=marker ai ts=4 sts=4 et sw=4 ft=python
