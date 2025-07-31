import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation
from collections import OrderedDict
from ckanext.alisea import helpers as h
import json
import ast
import logging

log = logging.getLogger(__name__)


class AliseaPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IPackageController, inherit=True)
    

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "alisea")


    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_google_tag': h.get_google_tag,
            'lao_current_url': h.lao_current_url,
        }

    def update_config_schema(self, schema):

        ignore_missing = toolkit.get_validator('ignore_missing')
        validators = [ignore_missing]
        schema.update({
            'footer_left': validators,
            'footer_right': validators,
        })

        return schema
    
    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        '''Add new search facet (filter) for datasets.
        This must be a field in the dataset (or organization or
        group if you're modifying those search facets, just change the function).
        '''
        # This keeps the existing facet order.
        facets_dict['country'] = plugins.toolkit._('Country')
        facets_dict['type_of_document'] = plugins.toolkit._('Document Type')
        facets_dict['language'] = plugins.toolkit._('Language')
        facets_dict['agroecology_category'] = plugins.toolkit._('Agroecology Category')
        facets_dict['agroecology_keyword'] = plugins.toolkit._('Agroecology Keyword')
        facets_dict['res_format'] = plugins.toolkit._('Format')

        
        return facets_dict
    
    
    def group_facets(self, facets_dict, group_type, package_type):
        # This keeps the existing facet order.

        facets_dict['country'] = plugins.toolkit._('Country')
        facets_dict['type_of_document'] = plugins.toolkit._('Document Type')
        facets_dict['language'] = plugins.toolkit._('Language')
        facets_dict['agroecology_category'] = plugins.toolkit._('Agroecology Category')
        facets_dict['agroecology_keyword'] = plugins.toolkit._('Agroecology Keyword')
        facets_dict['res_format'] = plugins.toolkit._('Format')
        
        return facets_dict
    
    def organization_facets(self, facets_dict, organization_type, package_type):

        facets_dict['country'] = plugins.toolkit._('Country')
        facets_dict['type_of_document'] = plugins.toolkit._('Document Type')
        facets_dict['language'] = plugins.toolkit._('Language')
        facets_dict['agroecology_category'] = plugins.toolkit._('Agroecology Category')
        facets_dict['agroecology_keyword'] = plugins.toolkit._('Agroecology Keyword')
        facets_dict['res_format'] = plugins.toolkit._('Format')
        
        return facets_dict
    
    # IPackageController
    def _before_index_dump_dicts(self, data_dict):
        """
        Converts dict fields in the data dictionary to JSON strings.

        This function is necessary to ensure that all fields in the data dictionary
        can be indexed by Solr. Solr cannot directly index fields of type dict, 
        which can lead to errors such as "missing required field" even when the 
        field is present in the data dictionary. By converting dict fields to JSON 
        strings, we ensure that the data is in a format that Solr can handle.

        This issue (https://github.com/ckan/ckan/issues/8423) has been observed in CKAN versions 2.10.4 and Solr 9, where 
        attempts to upload resources to the Datastore resulted in errors due to 
        the presence of dict fields in the data dictionary. The solution involves 
        transforming these fields into strings before indexing, as discussed in 
        the following issues:
        - CKAN - Custom plugin/theme error datastore using fluent presets https://github.com/ckan/ckan/issues/7750
        - Solr error: missing required field https://github.com/ckan/ckan/issues/7730

        Args:
            data_dict (dict): The data dictionary to be processed.

        Returns:
            dict: The processed data dictionary with dict fields as JSON strings.
        """
        for key, value in data_dict.items():
            if isinstance(value, dict):
                data_dict[key] = json.dumps(value)
        return data_dict

    def convert_stringified_lists(self, data_dict):
        """
        Converts stringified lists in the data dictionary to actual lists.
    
        Args:
            data_dict (dict): The data dictionary to be processed.
    
        Returns:
            dict: The processed data dictionary with actual lists.
    
        This function iterates over the items in the data dictionary and converts
        any stringified lists (strings that start with '[' and end with ']') into
        actual lists. Keys that start with 'extras_', 'res_', or are 'validated_data_dict'
        are excluded from this conversion.
        """
        # Excluded items
        excluded_keys = [
            key for key in data_dict 
            if key.startswith('extras_') or key.startswith('res_') or key == 'validated_data_dict'
        ]
    
        # Filter data dictionary
        filter_data_dict = {
            key: value for key, value in data_dict.items()
            if key not in excluded_keys
        }
    
        for key, value in filter_data_dict.items():
            if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                try:
                    data_dict[key] = ast.literal_eval(value)
                except (ValueError, SyntaxError) as e:
                    log.error("Error converting stringified list for key '%s': %s", key, e)
    
        return data_dict


    def before_dataset_index(self, data_dict):
        
        data_dict = self._before_index_dump_dicts(data_dict)
        data_dict = self.convert_stringified_lists(data_dict)
        data_dict['agroecology_category'] = json.loads(json.dumps(data_dict.get('agroecology_category', '[]')))
        data_dict['agroecology_keyword'] = json.loads(json.dumps(data_dict.get('agroecology_keyword', '[]')))

        return data_dict
