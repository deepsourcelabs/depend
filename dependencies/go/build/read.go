package main

/*
#include <stdlib.h>
*/
import "C"
import (
	"encoding/json"
	"unsafe"

	"golang.org/x/mod/modfile"
)

type goMod struct {
	Min_go_ver    string
	ModPath       string
	ModVer        string
	ModDeprecated string
	Dep_ver       []string
}

//export getDepVer
func getDepVer(filePtr *C.char) *C.char {
	// Analyzes go.mod contents for Dependency-Analyzer
	// go build -buildmode=c-shared -o _gomod.so
	file := C.GoString(filePtr)
	f, err := modfile.Parse("", []byte(file), nil)
	if err != nil {
		return C.CString("")
	}
	dep_ver := []string{}
	for _, dep := range f.Require {
		if len(dep.Mod.Path) > 0 {
			dep_ver = append(dep_ver, dep.Mod.Path+";"+dep.Mod.Version)
		}
	}
	var min_go_ver, modPath, modVer, modDeprecated string
	if f.Go != nil {
		min_go_ver = f.Go.Version
	}
	if f.Module != nil {
		modPath = f.Module.Mod.Path
		modVer = f.Module.Mod.Version
		modDeprecated = f.Module.Deprecated
	}
	retStruct := goMod{min_go_ver, modPath, modVer, modDeprecated, dep_ver}
	out, err := json.Marshal(retStruct)
	if err != nil {
		return C.CString("")
	}
	cstr := C.CString(string(out))
	return cstr
}

//export freeCByte
func freeCByte(b unsafe.Pointer) {
	C.free(b)
}

func main() {}
