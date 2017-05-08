ifeq ($(INSTALL_DIR),)
  $(error INSTALL_DIR is not set)
endif

busybox=busybox
adbd=adbd

.PHONY: install
install: $(busybox)
	mkdir -p $(INSTALL_DIR)
	cp $(busybox) $(INSTALL_DIR)
	cp $(adbd) $(INSTALL_DIR)

.PHONY: uninstall
uninstall:
	rm -fr $(INSTALL_DIR)

