// Copyright 2016-2018, Pulumi Corporation.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package convert

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/blang/semver"
	bridgetesting "github.com/pulumi/pulumi-terraform-bridge/v3/internal/testing"
	"github.com/pulumi/pulumi/pkg/v3/codegen/schema"
	"github.com/pulumi/pulumi/sdk/v3/go/common/tokens"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

type testLoader struct {
	path string
}

func (l *testLoader) LoadPackage(pkg string, version *semver.Version) (*schema.Package, error) {
	schemaPath := pkg
	if version != nil {
		schemaPath += "-" + version.String()
	}
	schemaPath = filepath.Join(l.path, schemaPath) + ".json"

	schemaBytes, err := os.ReadFile(schemaPath)
	if err != nil {
		return nil, err
	}

	var spec schema.PackageSpec
	err = json.Unmarshal(schemaBytes, &spec)
	if err != nil {
		return nil, err
	}

	schemaPackage, diags, err := schema.BindSpec(spec, l)
	if err != nil {
		return nil, err
	}
	if diags.HasErrors() {
		return nil, diags
	}

	return schemaPackage, nil
}

func (l *testLoader) LoadPackageReference(pkg string, version *semver.Version) (schema.PackageReference, error) {
	schemaPackage, err := l.LoadPackage(pkg, version)
	if err != nil {
		return nil, err
	}
	return schemaPackage.Reference(), nil
}

func isTruthy(s string) bool {
	return s == "1" || strings.EqualFold(s, "true")
}

func TestEject(t *testing.T) {
	// Test framework for eject
	// Each folder in testdata has a pcl folder, we check that if we convert the hcl we get the expected pcl
	// You can regenerate the test data by running "PULUMI_ACCEPT=1 go test" in this folder (pkg/tf2pulumi/convert).
	testDir, err := filepath.Abs(filepath.Join("testdata"))
	require.NoError(t, err)
	infos, err := os.ReadDir(testDir)
	require.NoError(t, err)

	tests := make([]struct {
		name string
		path string
	}, 0)
	for _, info := range infos {
		// Skip the "schemas" directory, that's for test schemas not for tests themselves
		if info.IsDir() && info.Name() != "schemas" && info.Name() != "mappings" {
			tests = append(tests, struct {
				name string
				path string
			}{
				name: info.Name(),
				path: filepath.Join(testDir, info.Name()),
			})
		}
	}

	loader := &testLoader{path: filepath.Join(testDir, "schemas")}
	mapper := &bridgetesting.TestFileMapper{Path: filepath.Join(testDir, "mappings")}

	for _, tt := range tests {
		tt := tt // avoid capturing loop variable in the closure

		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()

			hclPath := tt.path
			pclPath := filepath.Join(tt.path, "pcl")

			project, program, err := Eject(hclPath, loader, mapper)
			require.NoError(t, err)
			// Assert the project name is as expected (the directory name)
			assert.Equal(t, tokens.PackageName(tt.name), project.Name)

			// Assert every pcl file is seen
			infos, err := os.ReadDir(pclPath)
			if !os.IsNotExist(err) && !assert.NoError(t, err) {
				// If the directory was not found then the expected pcl results are the empty set, but if the
				// directory could not be read because of filesystem issues than just error out.
				assert.FailNow(t, "Could not read expected pcl results")
			}
			pclFiles := make(map[string]interface{})
			// infos will just be nil if pclPath did not exist
			for _, info := range infos {
				if !info.IsDir() {
					pclFiles[info.Name()] = nil
				}
			}

			// If PULUMI_ACCEPT is set then clear the PCL folder and write the generated files out
			if isTruthy(os.Getenv("PULUMI_ACCEPT")) {
				err := os.RemoveAll(pclPath)
				require.NoError(t, err)
				err = os.Mkdir(pclPath, 0700)
				require.NoError(t, err)
				for filename, source := range program.Source() {
					// normalize windows newlines to unix ones
					expectedPcl := []byte(strings.Replace(source, "\r\n", "\n", -1))
					err := os.WriteFile(filepath.Join(pclPath, filename), expectedPcl, 0600)
					require.NoError(t, err)
				}
			}

			// Assert the pcl source is as expected
			for filename, source := range program.Source() {
				pclBytes, err := os.ReadFile(filepath.Join(pclPath, filename))
				if assert.NoError(t, err) {
					// normalize windows newlines
					expectedPcl := strings.Replace(string(pclBytes), "\r\n", "\n", -1)
					source = strings.Replace(source, "\r\n", "\n", -1)
					assert.Equal(t, expectedPcl, source)
					delete(pclFiles, filename)
				}
			}

			unseenPcl := make([]string, 0)
			for name := range pclFiles {
				unseenPcl = append(unseenPcl, name)
			}
			assert.Empty(t, unseenPcl)
		})
	}
}