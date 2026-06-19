package execution

import (
	"fmt"
	"os"
	"path/filepath"

	cni "github.com/containerd/go-cni"
)

// raw embedded CNI config
const inlineCNIConfig = `{
  "cniVersion": "1.0.0",
  "name": "isolated-program-net",
  "plugins": [
    {
      "type": "bridge",
      "bridge": "cni-program0",
      "isGateway": true,
      "ipMasq": true,
      "ipam": {
        "type": "host-local",
        "subnet": "10.99.0.0/16",
        "routes": [{ "dst": "0.0.0.0/0" }]
      }
    },
    {
      "type": "portmap",
      "capabilities": {"portMappings": true}
    }
  ]
}`

func setupNetwork() (cni.CNI, string, error) {
	tmpNetCfgDir, err := os.MkdirTemp("", "cni-runtime-config-*")

	if err != nil {
		fmt.Errorf("[nsrunner] failed to create runtime config dir: %w", err)
		return nil, "", err
	}

	// write embedded config to temp folder
	configFilePath := filepath.Join(tmpNetCfgDir, "10-program-net.conflist")
	if err := os.WriteFile(configFilePath, []byte(inlineCNIConfig), 0644); err != nil {
		os.RemoveAll(tmpNetCfgDir)
		fmt.Errorf("[nsrunner] failed to write inline network config: %w", err)
		return nil, "", err
	}

	network, err := cni.New(
		cni.WithPluginDir([]string{"/opt/cni/bin"}),
		cni.WithPluginConfDir(tmpNetCfgDir),
		cni.WithConfListFile(configFilePath),
	)
	if err != nil {
		return nil, "", err
	}

	if err := network.Load(cni.WithAllConf); err != nil {
		return nil, "", err
	}

	return network, tmpNetCfgDir, nil
}
