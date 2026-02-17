define([
	'knockout',
	'jquery',
	'dropzone',
	'uuid',
	'arches',
	'viewmodels/alert-json',
	'bindings/dropzone',
	'templates/views/components/etl_modules/bulk-html-from-csv-exporter.htm',
], function(ko, $, dropzone, uuid, arches, JsonErrorAlertViewModel, dropzoneBinding, template) {
	const viewModel = function(params) {
		const self = this;

		// Common ETL params
		this.moduleId = params.etlmoduleid; // should match details.etlmoduleid in Python
		this.loadId = params.loadId || uuid.generate();
		this.loading = params.loading || ko.observable(false);
		this.alert = params.alert;
		this.state = params.state; // controls Task Details vs Task Status
		this.activeTab = params.activeTab || function(){}; // matches Branch Excel pattern
		// Status + polling data provided by parent ETL page
		this.loadDetails = params.load_details || ko.observable();
		this.selectedLoadEvent = params.selectedLoadEvent || ko.observable();

		// Local error message used when detailed load info is unavailable
		this.errorMessage = '';

		// File + CSV state
		// (Removed unused: fileInfo, fileAdded, csvFileName, resourceIds)

		// Backing form data (persist file for export)
		this.formData = new window.FormData();

		// Upload handler: immediately triggers export and switches to status tab
		this.addFile = function(file) {
			self.loading(true);
			self.formData.set('file', file, file.name);

			// Trigger export right away (server will parse CSV internally)
			self.submit('export').then(function() {
				// Switch to status tab like Branch Excel exporter
				if (typeof self.activeTab === 'function') { self.activeTab('import'); }
				// Move view to Task Status if parent provided `state`
				try { if (ko.isObservable(self.state)) { self.state('status'); } } catch (e) {}
			}).fail(function(err) {
				self.loadId = uuid.generate();
				console.log(err);
				// Capture a human-readable error for status view fallback
				try {
					const resp = err && err.responseJSON ? err.responseJSON : {};
					self.errorMessage = resp.message || resp.error || err.statusText || 'Unexpected error during export.';
				} catch (e) {
					self.errorMessage = 'Unexpected error during export.';
				}
				self.alert(new JsonErrorAlertViewModel('ep-alert-red', err.responseJSON, null, function(){}));
			}).always(function() {
				// Reset Task Details
				self.loading(false);
				try { if (self.dropzone) { self.dropzone.removeAllFiles(true); } } catch (e) {}
			});
		};

		// Cancel upload: clear dropzone and reset formData/loading
		this.cancelFileImport = function() {
			try { if (self.dropzone) { self.dropzone.removeAllFiles(true); } } catch (e) {}
			self.formData = new window.FormData();
			self.loadId = uuid.generate();
			self.loading(false);
		};

		// Helper to send actions to ETL manager (mirrors import-single-csv.js pattern)
		this.submit = function(action) {
			self.formData.set('action', action); // 'read' to parse CSV; 'export' to run export
			self.formData.set('load_id', self.loadId);
			self.formData.set('module', self.moduleId);
			return $.ajax({
				type: 'POST',
				url: arches.urls.etl_manager,
				data: self.formData,
				cache: false,
				processData: false,
				contentType: false,
			});
		};

		// (Removed unused formatSize helper)

		// Dropzone setup (single CSV upload)
		this.uniqueId = uuid.generate();
		this.uniqueidClass = ko.computed(function() { return 'unique_id_' + self.uniqueId; });
		this.dropzoneOptions = {
			url: 'arches.urls.root',
			dictDefaultMessage: '',
			autoProcessQueue: false,
			uploadMultiple: false,
			acceptedFiles: 'text/csv',
			autoQueue: false,
			clickable: '.fileinput-button.' + this.uniqueidClass(),
			previewsContainer: '#hidden-dz-previews',
			init: function() {
				self.dropzone = this;
				this.on('addedfile', self.addFile);
				this.on('error', function(file, error) { file.error = error; });
			}
		};
	};

	ko.components.register('bulk-html-from-csv-exporter', {
		viewModel: viewModel,
		template: template,
	});

	return viewModel;
});
