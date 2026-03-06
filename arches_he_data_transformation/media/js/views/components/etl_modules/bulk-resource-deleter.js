define([
	'knockout',
	'jquery',
	'dropzone',
	'uuid',
	'arches',
	'viewmodels/alert-json',
	'bindings/dropzone',
	'templates/views/components/etl_modules/bulk-resource-deleter.htm',
], function(ko, $, dropzone, uuid, arches, JsonErrorAlertViewModel, dropzoneBinding, template) {
	const viewModel = function(params) {
		this.moduleId = params.etlmoduleid;
		this.loadId = params.loadId || uuid.generate();
        this.transactionId = params.transactionId || uuid.generate();
		this.loading = params.loading || ko.observable(false);
		this.alert = params.alert;
		this.state = params.state;
		this.activeTab = params.activeTab || function(){};
		this.loadDetails = params.load_details || ko.observable();
		this.selectedLoadEvent = params.selectedLoadEvent || ko.observable();
		this.errorMessage = '';
		this.formData = new window.FormData();

		this.addFile = (file) => {
			this.loading(true);
			this.formData.set('file', file, file.name);

			this.submit('run_bulk_deletion').then(() => {
				if (typeof this.activeTab === 'function') {
					this.activeTab('import');
				}
				if (ko.isObservable(this.state)) {
					this.state('status');
				}
			}).fail((err) => {
				this.loadId = uuid.generate();
                this.transactionId = uuid.generate();
				console.log(err);
				const resp = err && err.responseJSON ? err.responseJSON : {};
				this.errorMessage = resp.message || resp.error || err.statusText || 'Unexpected error during deletion.';
				this.alert(new JsonErrorAlertViewModel('ep-alert-red', err.responseJSON, null, function(){}));
			}).always(() => {
				this.loading(false);
			});
		};

		this.submit = (action) => {
			this.formData.set('action', action);
			this.formData.set('load_id', this.loadId);
			this.formData.set('transaction_id', this.transactionId);
			this.formData.set('module', this.moduleId);
			return $.ajax({
				type: 'POST',
				url: arches.urls.etl_manager,
				data: this.formData,
				cache: false,
				processData: false,
				contentType: false,
			});
		};

		const addFileHandler = this.addFile.bind(this);

		this.uniqueId = uuid.generate();
		this.uniqueidClass = ko.computed(() => {
			return 'unique_id_' + this.uniqueId;
		});
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
				this.on('addedfile', addFileHandler);
				this.on('error', function(file, error) { file.error = error; });
			}
		};
	};

	ko.components.register('bulk-resource-deleter', {
		viewModel: viewModel,
		template: template,
	});

	return viewModel;
});
