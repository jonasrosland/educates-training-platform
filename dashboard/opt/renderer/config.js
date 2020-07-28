var path = require('path');
var fs = require('fs');
var yaml = require('js-yaml');

var base_url = process.env.URI_ROOT_PATH || '';

var config = {
    // Log format for messages and request logging.

    log_format: process.env.LOG_FORMAT || 'dev',

    // Port that the application server listens on.

    server_port: parseInt(process.env.PORT || '8080'),

    // Prefix when hosting site at a sub URL.

    base_url: base_url,

    // Specifies the path of workshop folder where the workshop
    // files are located. This will be overridden down below to
    // look in other valid places that content can be kept.

    workshop_dir: path.join(__dirname, 'workshop'),

    // Specifies the path of config file for workshop. This will
    // be overridden down below to look in other valid places
    // that content can be kept.

    config_file: path.join(__dirname, 'workshop', 'config.js'),

    // Specifies the path of content folder where all content
    // files are located. This will be overridden down below to
    // look in other valid places that content can be kept.

    content_dir: path.join(__dirname, 'workshop', 'content'),

    // URL where the users should be redirected to restart the
    // workshop when they reach the final page.

    restart_url: process.env.RESTART_URL,

    // Site title. Appears in page banner.

    site_title: 'eduk8s',

    // Training portal, workshop and session configuration.

    workshop_name: process.env.WORKSHOP_NAME || '',
    session_namespace: process.env.SESSION_NAMESPACE || '',
    workshop_namespace: process.env.WORKSHOP_NAMESPACE || '',
    training_portal: process.env.TRAINING_PORTAL || '',
    ingress_domain: process.env.INGRESS_DOMAIN || '',
    ingress_protocol: process.env.INGRESS_PROTOCOL || '',

    // Google analytics tracking ID.

    google_tracking_id: process.env.GOOGLE_TRACKING_ID || '',

    // Where no list of modules is defined, and the default page
    // exists it will be added to the list of modules. If the page
    // is Markdown, it will be processed and meta data used to
    // try and determine all modules in the navigation path.

    default_page: 'index',

    // List of workshop modules. Can define 'path' to page,
    // without extension. The page can either be Markdown (.md)
    // or AsciiDoc (.adoc). Name of page should be give by
    // 'title'. Any title in Markdown meta data will be ignored.
    // Any document title in an AsciiDoc page will be ignored.
    // If not title is given it will be generated from name of
    // file. Label on the button to go to next page can be
    // overridden by 'exit_sign'. For the final page, can define
    // 'exit_link', if need to send users off site, otherwise
    // should never be defined.

    modules: [
        /*
        {
            'path': 'index',
            'title': 'Workshop Overview',
            'exit_sign': 'Setup Workshop',
        },
        {
            'path': 'setup',
            'title': 'Workshop Setup',
            'exit_sign': 'Start Workshop',
        },
        {
            'path': 'exercies/step-1',
            'title': 'User Steps 1',
        },
        {
            'path': 'exercies/step-2',
            'title': 'User Steps 2',
            'exit_sign': 'Finish Workshop',
        },
        {
            'path': 'finish',
            'title': 'Workshop Finished',
            'exit_sign': 'Start Workshop',
        },
        */
    ],

    // List of variables available for interpolation in content.
    // Where a user supplied config.js provides variables,
    // entries from it will be appended to these.

    variables: [
      {
        name: 'workshop_name',
        content: ((process.env.WORKSHOP_NAME=== undefined)
            ? '' : process.env.WORKSHOP_NAME)
      },
      {
        name: 'session_namespace',
        content: ((process.env.SESSION_NAMESPACE === undefined)
            ? '' : process.env.SESSION_NAMESPACE)
      },
      {
        name: 'workshop_namespace',
        content: ((process.env.WORKSHOP_NAMESPACE === undefined)
            ? '' : process.env.WORKSHOP_NAMESPACE)
      },
      {
        name: 'training_portal',
        content: ((process.env.TRAINING_PORTAL === undefined)
            ? '' : process.env.TRAINING_PORTAL)
      },
      {
        name: 'ingress_domain',
        content: ((process.env.INGRESS_DOMAIN === undefined)
            ? '' : process.env.INGRESS_DOMAIN)
      },
      {
        name: 'ingress_protocol',
        content: ((process.env.INGRESS_PROTOCOL === undefined)
            ? 'http' : process.env.INGRESS_PROTOCOL)
      },
    ],
};

if (process.env.ENABLE_TERMINAL == 'true') {
    config.variables.push({
        name: 'terminal_url',
        content: path.join(base_url, '..', 'terminal')
    });
}

if (process.env.ENABLE_SLIDES == 'true') {
    config.variables.push({
        name: 'slides_url',
        content: path.join(base_url,'..', 'slides')
    });
}

if (process.env.ENABLE_CONSOLE_KUBERNETES == 'true') {
    config.variables.push({
        name: 'console_url',
        content: path.join(base_url, '..', 'console')
    });
}

if (process.env.ENABLE_REGISTRY == 'true') {
    config.variables.push({
        name: 'registry_host',
        content: ((process.env.REGISTRY_HOST === undefined)
            ? '' : process.env.REGISTRY_HOST)
    });
    config.variables.push({
        name: 'registry_auth_file',
        content: ((process.env.REGISTRY_AUTH_FILE === undefined)
            ? '' : process.env.REGISTRY_AUTH_FILE)
    });
    config.variables.push({
        name: 'registry_username',
        content: ((process.env.REGISTRY_USERNAME === undefined)
            ? '' : process.env.REGISTRY_USERNAME)
    });
    config.variables.push({
        name: 'registry_password',
        content: ((process.env.REGISTRY_PASSWORD === undefined)
            ? '' : process.env.REGISTRY_PASSWORD)
    });
    config.variables.push({
        name: 'registry_secret',
        content: ((process.env.REGISTRY_SECRET === undefined)
            ? '' : process.env.REGISTRY_SECRET)
    });
}

for (let key in process.env) {
    config.variables.push({
        name: 'ENV_'+ key,
        content: process.env[key]
    });
}

// Check various locations for content and config.

var workshop_file = process.env.WORKSHOP_FILE || 'workshop.yaml';

var workshop_dir = process.env.WORKSHOP_DIR;

if (workshop_dir && fs.existsSync(path.join(workshop_dir, 'content'))) {
    config.workshop_dir = workshop_dir;
    config.config_file = path.join(config.workshop_dir, 'config.js');
    config.content_dir = path.join(config.workshop_dir, 'content');
}
else {
    workshop_dir = '/opt/eduk8s/workshop';

    if (fs.existsSync(path.join(workshop_dir, 'content'))) {
        config.workshop_dir = workshop_dir;
        config.config_file = path.join(config.workshop_dir, 'config.js');
        config.content_dir = path.join(config.workshop_dir, 'content');
    }
    else {
        workshop_dir = '/opt/workshop';

        if (fs.existsSync(path.join(workshop_dir, 'content'))) {
            config.workshop_dir = workshop_dir;
            config.config_file = path.join(config.workshop_dir, 'config.js');
            config.content_dir = path.join(config.workshop_dir, 'content');
        }
        else {
            workshop_dir = '/home/eduk8s/workshop';

            if (fs.existsSync(path.join(workshop_dir, 'content'))) {
                config.workshop_dir = workshop_dir;
                config.config_file = path.join(config.workshop_dir, 'config.js');
                config.content_dir = path.join(config.workshop_dir, 'content');
            }
        }
    }
}

// If user config.js is supplied with alternate content, merge
// it with the configuration above.

function process_workshop_config(workshop_config) {
    if (workshop_config === undefined) {
        workshop_config = require(config.config_file);
    }

    if (typeof workshop_config != 'function') {
        return workshop_config;
    }

    var temp_config = {
        site_title: "eduk8s",

        google_tracking_id: "",

        modules: [],

        variables: [],
    };

    function site_title(title) {
        temp_config.site_title = title;
    }

    function google_tracking_id(id) {
        if (id) {
            temp_config.google_tracking_id = id;
        }
    }

    function module_metadata(pathname, title, exit_sign) {
        temp_config.modules.push({
            path: pathname,
            title: title,
            exit_sign: exit_sign,
        });
    }

    function data_variable(name, value, aliases) {
        if (typeof aliases == "string") {
            aliases = [aliases];
        }
        if (aliases !== undefined) {
            for (let i = 0; i < aliases.length; i++) {
                let alias = aliases[i];
                if (process.env[alias] !== undefined) {
                    value = process.env[alias];
                    break;
                }
            }
        }
        else {
            if (process.env[name] !== undefined) {
                value = process.env[name];
            }
        }

        temp_config.variables.push({
            name: name,
            content: value
        });
    }

    function load_workshop(pathname) {
        if (pathname === undefined) {
            pathname = workshop_file;
        }

        // Read the workshops file first to get the site title
        // and list of activated workshops.

        pathname = path.join(config.workshop_dir, pathname);

        let workshop_data = fs.readFileSync(pathname, 'utf8');
        let workshop_info = yaml.safeLoad(workshop_data);

        temp_config.site_title = workshop_info.name;

        // Now iterate over list of activated modules and populate
        // modules list in config.

        pathname = path.join(config.workshop_dir, 'modules.yaml');

        let modules_data = fs.readFileSync(pathname, 'utf8');
        let modules_info = yaml.safeLoad(modules_data);

        for (let i = 0; i < workshop_info.modules.activate.length; i++) {
            let name = workshop_info.modules.activate[i];
            let module_info = modules_info.modules[name];

            if (module_info) {
                module_metadata(name, module_info.name, module_info.exit_sign);
            }
        }

        // Next set data variables and any other config settings
        // from the modules file.

        let modules_conf = modules_info.config || {};

        google_tracking_id(modules_conf.google_tracking_id);

        let variables_set = new Set();

        if (modules_conf.vars) {
            for (let i = 0; i < modules_conf.vars.length; i++) {
                let vars_info = modules_conf.vars[i];

                let name = vars_info.name;
                let value = vars_info.value;
                let aliases = vars_info.aliases;

                // We override default value with that from the
                // workshop file if specified.

                if (workshop_info.vars) {
                    if (workshop_info.vars[name] !== undefined) {
                        value = workshop_info.vars[name];
                    }
                }

                variables_set.add(name);

                data_variable(name, value, aliases);
            }
        }

        // Now override any data variables from the workshop file
        // if haven't already added them.

        if (workshop_info.vars) {
            for (let name in workshop_info.vars) {
                if (!variables_set.has(name)) {
                    data_variable(name, workshop_info.vars[name]);
                }
            }
        }
    }

    var workshop = {
        config: temp_config,
        site_title: site_title,
        google_tracking_id: google_tracking_id,
        module_metadata: module_metadata,
        data_variable: data_variable,
        load_workshop: load_workshop,
    }

    workshop_config(workshop);

    return temp_config;
}

const allowed_config = new Set([
    'site_title',
    'modules',
    'variables',
]);

function initialize_workshop() {
    var override_config;

    if (fs.existsSync(config.config_file)) {
        // User provided config.js file.

        var override_config = process_workshop_config();
    }
    else {
        // User provided workshop.yaml file.

        let file = path.join(config.workshop_dir, workshop_file);

        if (fs.existsSync(file)) {
            function initialize_workshop_file(workshop) {
                workshop.load_workshop(workshop_file);
            }

            override_config = process_workshop_config(initialize_workshop_file);
        }
    }

    if (override_config) {
        for (var key1 in override_config) {
            if (allowed_config.has(key1)) {
                var value1 = override_config[key1];
                if (value1 !== undefined && value1 != null) {
                    if (value1.constructor == Array) {
                        config[key1] = config[key1].concat(value1);
                    }
                    else if (value1.constructor == Object) {
                        for (var key2 in value1) {
                            config[key1][key2] = value1[key2];
                        }
                    }
                    else {
                        config[key1] = value1;
                    }
                }
            }
        }
    }
}

exports.default = {
    config,
    initialize_workshop,
}

module.exports = exports.default;